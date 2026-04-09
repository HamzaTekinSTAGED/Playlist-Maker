"""
Step 1: YouTube'dan ses indir ve segmentlere böl.
Notebook Cell 1'in düzeltilmiş versiyonu.
"""
import os
import yt_dlp
from pydub import AudioSegment

# === CONFIG ===
YOUTUBE_URL = "https://www.youtube.com/watch?v=1wKRcLsGfBg"
OUTPUT_DIR = "output"
SEGMENTS_DIR = os.path.join(OUTPUT_DIR, "segments")

START_OFFSET = 9 * 1000       # 9 saniye
SEGMENT_LENGTH = 11 * 1000    # 11 saniye
STEP = 13 * 1000              # 13 saniye

os.makedirs(SEGMENTS_DIR, exist_ok=True)


# === 1. VIDEO DOWNLOAD ===
def download_audio():
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{OUTPUT_DIR}/audio.%(ext)s',
        'cookiefile': 'cookies.txt',

        # JS challenge çözümü
        'js_runtimes': {
            'node': {}
        },
        'remote_components': ['ejs:github'],

        'geo_bypass': True,

        # ffmpeg path
        'ffmpeg_location': 'C:\\ffmpeg\\bin',

        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([YOUTUBE_URL])

    return f"{OUTPUT_DIR}/audio.wav"


# === 2. SEGMENTATION ===
def create_segments(audio_path):
    audio = AudioSegment.from_wav(audio_path)
    duration = len(audio)

    segments_info = []
    current = START_OFFSET
    index = 1

    while current + SEGMENT_LENGTH < duration:
        segment = audio[current:current + SEGMENT_LENGTH]

        filename = f"{SEGMENTS_DIR}/segment_{index}.wav"
        segment.export(filename, format="wav")

        start_sec = current / 1000
        end_sec = (current + SEGMENT_LENGTH) / 1000

        segments_info.append({
            "index": index,
            "file": filename,
            "start": start_sec,
            "end": end_sec
        })

        current += STEP
        index += 1

    return segments_info


# === 3. SAVE TIMESTAMPS ===
def save_timestamps(segments_info):
    txt_path = os.path.join(OUTPUT_DIR, "timestamps.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segments_info:
            f.write(f"{seg['index']}. {seg['start']:.2f}s - {seg['end']:.2f}s\n")

    print(f"Timestamps saved: {txt_path}")


# === RUN ===
if __name__ == "__main__":
    audio_path = download_audio()
    segments = create_segments(audio_path)
    save_timestamps(segments)

    print(f"Total segments: {len(segments)}")
