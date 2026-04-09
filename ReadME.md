# YouTube to Spotify Playlist Maker

There are videos on YouTube that play 10-second clips from old songs, which create a nostalgic feeling. While watching one of these videos, I wanted to have a Spotify playlist made only from the songs in that video. So I designed this script for that purpose. It takes 10-second fragments from the full audio and identifies each song. After identifying all the songs, it creates a .txt list of them. If you provide your Spotify credentials in the terminal, the script automatically creates a playlist from that list.


This project automatically identifies songs in a YouTube video and creates a new Spotify playlist from them.

Workflow:
- Downloads audio from the YouTube video.
- Splits the audio into small clips (segments).
- Identifies each segment with ACRCloud.
- Writes recognized songs to `output/songs_detected.txt`.
- Creates a Spotify playlist from that list via the Spotify API.

## Project Structure

- `step1_download_and_segment.py`: Downloads YouTube audio and creates segments.
- `step2_recognize_songs.py`: Identifies segments with ACRCloud and creates the song list file.
- `main.py`: Creates a Spotify playlist and adds songs.
- `output/`: Generated audio, segment, and text output files.

## Requirements

- Python 3.10+
- ffmpeg (Windows example: `C:\ffmpeg\bin`)
- Spotify Developer app (Client ID / Client Secret)
- ACRCloud project (Access Key / Access Secret)
- (Optional, may be required for step1) `cookies.txt`

Python packages:
- `spotipy`
- `yt-dlp`
- `pydub`
- `requests`

Example installation:

```bash
pip install spotipy yt-dlp pydub requests
```

## Setup Notes

1. Update `YOUTUBE_URL` in `step1_download_and_segment.py` with your target video URL.
2. If needed, adjust `ffmpeg_location` in the script to match your environment.
3. Set Spotify environment variables:

```powershell
$env:SPOTIFY_CLIENT_ID="your_client_id"
$env:SPOTIFY_CLIENT_SECRET="your_client_secret"
```

4. The Spotify Redirect URI in `main.py` is:
   - `http://127.0.0.1:8080/callback`
   - You must register this exact URI in your Spotify Developer Dashboard.

## Run Order

```bash
python step1_download_and_segment.py
python step2_recognize_songs.py
python main.py
```

## Output Files

- `output/audio.wav`: downloaded source audio
- `output/segments/segment_*.wav`: generated audio segments
- `output/timestamps.txt`: segment timestamps
- `output/songs_detected.txt`: recognized song list
- Spotify playlist URL: printed in terminal at the end of `main.py`

## Important Note

ACRCloud keys are currently hardcoded in `step2_recognize_songs.py`. For better security, move them to environment variables.