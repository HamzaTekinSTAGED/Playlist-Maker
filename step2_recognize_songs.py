"""
Step 2: Segmentleri ACRCloud ile tanı ve songs_detected.txt oluştur.
Notebook Cell 2 & 3'ün düzeltilmiş versiyonu.

Düzeltilen hatalar:
  1. Segment sıralama: lexicographic → numeric (segment_1, segment_2, ... segment_100)
  2. File handle leak: open() dosyası artık with bloğunda kapatılıyor
  3. Timestamp format: :05.2f → :.2f (4+ haneli sayılarda taşma düzeltildi)
"""
import os
import requests
import json
import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode

# === CONFIG ===
SEGMENTS_DIR = "output/segments"
OUTPUT_TXT = "output/songs_detected.txt"

HOST = "identify-ap-southeast-1.acrcloud.com"
ACCESS_KEY = "c190d1cfdc7fdd482567d1e56a7b33fe"
ACCESS_SECRET = "GfpVh5An21PiM3deCTNV50ayJCdB5tNSzSURH1KJ"


def recognize_file(file_path):
    """ACRCloud ile ses dosyasını tanı."""
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([
        http_method, http_uri, ACCESS_KEY,
        data_type, signature_version, timestamp
    ])
    sign = base64.b64encode(
        hmac.new(
            ACCESS_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha1
        ).digest()
    ).decode('utf-8')

    # FIX: File handle leak — with bloğu ile dosya otomatik kapanır
    with open(file_path, 'rb') as audio_file:
        files = {'sample': audio_file}
        payload = {
            'access_key': ACCESS_KEY,
            'data_type': data_type,
            'signature_version': signature_version,
            'signature': sign,
            'timestamp': timestamp
        }

        response = requests.post(
            f'https://{HOST}{http_uri}',
            files=files,
            data=payload
        )

    data = response.json()

    if 'metadata' in data and 'music' in data['metadata']:
        music = data['metadata']['music'][0]
        song_name = music.get('title', 'UNKNOWN')
        artist = music.get('artists', [{'name': 'UNKNOWN'}])[0]['name']
        return song_name, artist, True
    else:
        return 'UNKNOWN', 'UNKNOWN', False


def main():
    # FIX: Numeric sorting — segment_1, segment_2, ..., segment_10, ..., segment_100
    # Eski kod: sorted(os.listdir(...)) → segment_1, segment_10, segment_100, segment_11 (YANLIŞ!)
    segment_files = sorted(
        os.listdir(SEGMENTS_DIR),
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )

    results = []
    total = len(segment_files)

    for i, file in enumerate(segment_files, 1):
        file_path = os.path.join(SEGMENTS_DIR, file)
        print(f"[{i}/{total}] Recognizing: {file}")
        song, artist, ok = recognize_file(file_path)
        if ok:
            print(f"  ✓ {song} - {artist}")
        else:
            print(f"  ✗ Tanınamadı")
        results.append((file, song, artist, ok))

    # TXT yaz
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for r in results:
            index = int(r[0].split('_')[1].split('.')[0])
            start_sec = 9 + (index - 1) * 13
            end_sec = start_sec + 11
            check = '✓' if r[3] else '✗'
            # FIX: Format genişliği kaldırıldı — :05.2f yerine :.2f
            # Eski: f"{start_sec:05.2f}" → "09.00" ama "1296.00" 7 karakter olur (taşma)
            f.write(f"{start_sec:.2f} - {end_sec:.2f} | {r[1]} - {r[2]} {check}\n")

    print(f"\nRecognition completed. TXT saved: {OUTPUT_TXT}")
    print(f"Toplam: {total} segment, {sum(1 for r in results if r[3])} tanındı, "
          f"{sum(1 for r in results if not r[3])} tanınamadı")


if __name__ == "__main__":
    main()
