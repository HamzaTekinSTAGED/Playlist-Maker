# Before running this code make sure that you ran youtube_to_txt.ipynb.
# youtube_to_txt.ipynb will create a txt file with the songs that were detected in the YouTube video.




# This code will create a playlist on Spotify with the songs that were detected in the YouTube video.
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyOauthError
from spotipy.exceptions import SpotifyException
import os
import webbrowser
import json
import time
import hashlib
import requests



# === CONFIG ===
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")



SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:8080/callback'
SCOPE = 'playlist-modify-public playlist-modify-private'
PLAYLIST_NAME = 'BOyeaz Playlist'
TXT_FILE = 'output/songs_detected.txt'
CACHE_PATH = ".spotify_cache_main"
REQUIRED_SCOPES = {"playlist-modify-public", "playlist-modify-private"}
DEBUG_LOG_PATH = "debug-b2e846.log"
RUN_ID = f"run-{int(time.time() * 1000)}"


def debug_log(hypothesis_id, location, message, data):
    # #region agent log
    payload = {
        "sessionId": "b2e846",
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")
    # #endregion

# === CACHE TEMİZLE (eski token sorunlarını önler) ===
if os.path.exists(CACHE_PATH):
    os.remove(CACHE_PATH)
    print("Old token cache removed.")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("\nERROR: SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET ortam degiskenleri tanimli degil.")
    print("PowerShell icin ornek:")
    print('  $env:SPOTIFY_CLIENT_ID="your_client_id"')
    print('  $env:SPOTIFY_CLIENT_SECRET="your_client_secret"')
    exit(1)

# === 1. SPOTIFY AUTH ===
print("=" * 50)
print("YouTube -> Spotify Playlist Maker")
print("=" * 50)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH,
    show_dialog=True,
    open_browser=False
))
# #region agent log
debug_log("N1", "main.py:56", "auth manager init", {"client_id_suffix": SPOTIFY_CLIENT_ID[-6:] if SPOTIFY_CLIENT_ID else None, "redirect_uri": SPOTIFY_REDIRECT_URI, "scope": SCOPE})
# #endregion

# Kullanici bilgilerini al
try:
    me = sp.me()
except SpotifyOauthError:
    # #region agent log
    debug_log("N6", "main.py:76", "SpotifyOauthError on sp.me()", {"error_type": "SpotifyOauthError"})
    # #endregion
    print("\nERROR: OAuth dogrulamasi basarisiz oldu.")
    print("Bu hata genelde Spotify uygulamasi auth'u devraldiginda gorulur (AudienceMismatch).")
    print("Cozum:")
    print("1) Scriptin verdigi authorize URL'i Chrome/Edge'de acin (Spotify app'te degil).")
    print("2) Redirect URI'nin Spotify Dashboard'da birebir kayitli oldugunu kontrol edin.")
    print("3) Gerekirse tarayicida farkli hesapla tekrar izin verin.")
    exit(1)
except SpotifyException as exc:
    # #region agent log
    token_info_on_me_fail = sp.auth_manager.cache_handler.get_cached_token()
    token_scope_on_me_fail = token_info_on_me_fail.get("scope", "") if token_info_on_me_fail else ""
    token_hash_on_me_fail = None
    if token_info_on_me_fail and token_info_on_me_fail.get("access_token"):
        token_hash_on_me_fail = hashlib.sha256(token_info_on_me_fail["access_token"].encode("utf-8")).hexdigest()[:12]
    debug_log(
        "N7",
        "main.py:84",
        "SpotifyException on sp.me()",
        {
            "status": exc.http_status,
            "msg": str(exc)[:180],
            "has_cached_token": bool(token_info_on_me_fail),
            "scope_on_fail": token_scope_on_me_fail,
            "token_hash12_on_fail": token_hash_on_me_fail,
            "expires_at_on_fail": token_info_on_me_fail.get("expires_at") if token_info_on_me_fail else None,
            "now": int(time.time()),
        },
    )
    if token_info_on_me_fail and token_info_on_me_fail.get("access_token"):
        probe_headers = {"Authorization": f"Bearer {token_info_on_me_fail['access_token']}"}
        me_probe = requests.get("https://api.spotify.com/v1/me", headers=probe_headers, timeout=20)
        debug_log(
            "N8",
            "main.py:102",
            "probe GET /me after sp.me() failure",
            {
                "status_code": me_probe.status_code,
                "www_authenticate": me_probe.headers.get("WWW-Authenticate"),
                "body_snippet": me_probe.text[:160],
            },
        )
    # #endregion
    if exc.http_status == 401 and token_info_on_me_fail and token_info_on_me_fail.get("access_token"):
        # #region agent log
        debug_log("N9", "main.py:122", "fallback /me via direct requests", {"trigger_status": exc.http_status})
        # #endregion
        direct_headers = {"Authorization": f"Bearer {token_info_on_me_fail['access_token']}"}
        direct_me_resp = requests.get("https://api.spotify.com/v1/me", headers=direct_headers, timeout=20)
        # #region agent log
        debug_log("N9", "main.py:127", "direct /me fallback result", {"status_code": direct_me_resp.status_code, "body_snippet": direct_me_resp.text[:160]})
        # #endregion
        if direct_me_resp.status_code == 200:
            me = direct_me_resp.json()
        else:
            raise
    else:
        raise
user_id = me['id']
print(f"\nLogin successful! User: {me.get('display_name', user_id)} ({user_id})")

token_info = sp.auth_manager.cache_handler.get_cached_token()
token_scope = set(token_info.get("scope", "").split()) if token_info else set()
missing_scopes = REQUIRED_SCOPES - token_scope
# #region agent log
access_token = token_info.get("access_token") if token_info else None
token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:12] if access_token else None
expires_at = token_info.get("expires_at") if token_info else None
debug_log("N2", "main.py:79", "token snapshot", {"has_token": bool(token_info), "token_hash12": token_hash, "expires_at": expires_at, "now": int(time.time()), "missing_scopes": sorted(missing_scopes)})
# #endregion
print(f"Token scope: {' '.join(sorted(token_scope)) if token_scope else 'YOK'}")

if missing_scopes:
    print("\nERROR: Token icinde eksik yetki(ler) var:")
    print(f"   {', '.join(sorted(missing_scopes))}")
    print("Cozum:")
    print("1) Tarayicida izin ekranini tekrar onaylayin.")
    print("2) Spotify Dashboard > App settings > Redirect URI eslesmesini kontrol edin.")
    print("3) Gerekirse cache dosyasini silip tekrar deneyin.")
    exit(1)

# #region agent log
if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}
    probe_resp = requests.get("https://api.spotify.com/v1/me/playlists?limit=1", headers=headers, timeout=20)
    debug_log("N3", "main.py:95", "probe GET /me/playlists", {"status_code": probe_resp.status_code, "www_authenticate": probe_resp.headers.get("WWW-Authenticate"), "body_snippet": probe_resp.text[:140]})
# #endregion

# === 2. PLAYLIST OLUŞTUR ===
print(f"\nCreating playlist: '{PLAYLIST_NAME}'...")
try:
    playlist = sp.user_playlist_create(user=user_id, name=PLAYLIST_NAME, public=True)
except SpotifyException as exc:
    # #region agent log
    debug_log("N4", "main.py:102", "user_playlist_create failed", {"status": exc.http_status, "msg": str(exc)[:180]})
    # #endregion
    if exc.http_status in (401, 403):
        playlist_payload = {"name": PLAYLIST_NAME, "public": False}
        try:
            playlist = sp._post("me/playlists", payload=playlist_payload)
        except SpotifyException as fallback_exc:
            # #region agent log
            debug_log("N5", "main.py:108", "fallback me/playlists failed", {"status": fallback_exc.http_status, "msg": str(fallback_exc)[:180]})
            # #endregion
            direct_token_info = sp.auth_manager.cache_handler.get_cached_token()
            direct_access = direct_token_info.get("access_token") if direct_token_info else None
            if direct_access:
                # #region agent log
                debug_log("N10", "main.py:178", "direct POST /me/playlists fallback attempt", {"trigger_statuses": [exc.http_status, fallback_exc.http_status]})
                # #endregion
                direct_headers = {
                    "Authorization": f"Bearer {direct_access}",
                    "Content-Type": "application/json",
                }
                direct_resp = requests.post(
                    "https://api.spotify.com/v1/me/playlists",
                    headers=direct_headers,
                    json=playlist_payload,
                    timeout=20,
                )
                # #region agent log
                debug_log("N10", "main.py:190", "direct POST /me/playlists result", {"status_code": direct_resp.status_code, "www_authenticate": direct_resp.headers.get("WWW-Authenticate"), "body_snippet": direct_resp.text[:180]})
                # #endregion
                if direct_resp.status_code in (200, 201):
                    playlist = direct_resp.json()
                else:
                    print(f"\nERROR: Spotify playlist olusturma basarisiz ({exc.http_status} -> fallback {fallback_exc.http_status} -> direct {direct_resp.status_code}).")
                    print("Token gecerli ve scope dogru, ancak hesap/app policy olusturmaya izin vermiyor olabilir.")
                    print("Kontrol:")
                    print("1) Spotify Dashboard'da uygulama user management listesinde bu hesap var mi?")
                    print("2) Uygulama dogru client_id ile calisiyor mu?")
                    print("3) Hesapta playlist olusturma kisiti var mi?")
                    exit(1)
            else:
                print(f"\nERROR: Spotify playlist olusturma basarisiz ({exc.http_status} -> fallback {fallback_exc.http_status}).")
                print("Token gecerli ve scope dogru, ancak hesap/app policy olusturmaya izin vermiyor olabilir.")
                print("Kontrol:")
                print("1) Spotify Dashboard'da uygulama user management listesinde bu hesap var mi?")
                print("2) Uygulama dogru client_id ile calisiyor mu?")
                print("3) Hesapta playlist olusturma kisiti var mi?")
                exit(1)
    else:
        raise
playlist_id = playlist['id']
print(f"Playlist created! ID: {playlist_id}")

# === 3. TXT DOSYASINI OKU VE SPOTIFY'DA ARA ===
if not os.path.exists(TXT_FILE):
    print(f"\nERROR: File not found: {TXT_FILE}")
    print("Run step2_recognize_songs.py first.")
    exit(1)

print(f"\nSearching songs ({TXT_FILE})...")
uris = []
not_found = []

with open(TXT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or '✓' not in line:
            continue
        parts = line.split('|')
        if len(parts) < 2:
            continue
        song_info = parts[1].split('✓')[0].strip()
        if ' - ' in song_info:
            song_name, artist = song_info.split(' - ', 1)
        else:
            song_name = song_info
            artist = ''

        query = f"track:{song_name} artist:{artist}"
        result = sp.search(q=query, type='track', limit=1)
        tracks = result['tracks']['items']
        if tracks:
            uris.append(tracks[0]['uri'])
            print(f"  OK {song_name.strip()} - {artist.strip()}")
        else:
            not_found.append(f"{song_name.strip()} - {artist.strip()}")
            print(f"  NOT_FOUND: {song_name.strip()} - {artist.strip()}")

# === 4. PLAYLIST'E EKLE ===
if uris:
    # Spotify max 100 şarkı per request
    for i in range(0, len(uris), 100):
        batch = uris[i:i+100]
        sp.playlist_add_items(playlist_id, batch)

    playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
    print(f"\n{'=' * 50}")
    print(f"Completed! {len(uris)} songs added.")
    if not_found:
        print(f"Warning: {len(not_found)} songs were not found on Spotify.")
    print(f"Playlist URL: {playlist_url}")
    print(f"{'=' * 50}")

    # Spotify'da aç
    webbrowser.open(playlist_url)
else:
    print("\nERROR: No songs found.")