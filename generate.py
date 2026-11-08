
import os
import json
import time
import subprocess
import requests
from pathlib import Path
from google import genai
from gtts import gTTS

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

client = genai.Client(api_key=GEMINI_KEY)

Path("content").mkdir(exist_ok=True)
Path("videos").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)

prompt = """
Create exactly 9 original viral-style TikTok video concepts.
Use a mixture of facts, life hacks, funny moments, motivation,
technology, animals, discoveries, storytelling and entertainment.

Return ONLY valid JSON in this exact structure:
{
  "videos": [
    {
      "title": "Short title",
      "hook": "Opening sentence",
      "script": "20 to 30 second spoken script",
      "visual_search": "2 or 3 simple Pixabay search words",
      "caption": "TikTok caption",
      "hashtags": "#tag1 #tag2 #tag3"
    }
  ]
}

Make exactly 9 different videos.
Use accurate facts and natural English.
No copyrighted characters or invented statistics.
"""

print("Generating 9 video scripts...")

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
    config={"response_mime_type": "application/json"}
)

data = json.loads(response.text)
items = data["videos"]

if len(items) != 9:
    raise ValueError("Gemini did not return exactly 9 videos.")

def get_duration(audio):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio)
        ],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())

def timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}".replace(".", ",")

def make_subtitles(text, duration, path):
    words = text.split()
    chunks = [
        words[i:i + 7]
        for i in range(0, len(words), 7)
    ]

    total = max(len(words), 1)
    lines = []
    word_position = 0

    for number, chunk in enumerate(chunks, 1):
        start = duration * word_position / total
        word_position += len(chunk)
        end = duration * word_position / total

        lines.extend([
            str(number),
            f"{timestamp(start)} --> {timestamp(end)}",
            " ".join(chunk),
            ""
        ])

    path.write_text("\n".join(lines), encoding="utf-8")

def get_pixabay_video(query, output):
    try:
        result = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": PIXABAY_KEY,
                "q": query,
                "per_page": 5
            },
            timeout=30
        )
        result.raise_for_status()

        hits = result.json().get("hits", [])
        if not hits:
            return False

        files = hits[0].get("videos", {})
        video = files.get("large") or files.get("medium")

        if not video or not video.get("url"):
            return False

        download = requests.get(
            video["url"], timeout=60
        )
        download.raise_for_status()
        output.write_bytes(download.content)

        return output.stat().st_size > 10000

    except Exception as error:
        print("Pixabay error:", error)
        return False

def render_video(item, number):
    title = item["title"]
    spoken_text = item["hook"] + " " + item["script"]

    audio = Path(f"temp/audio_{number}.mp3")
    background = Path(f"temp/background_{number}.mp4")
    subtitles = Path(f"temp/subtitles_{number}.srt")
    output = Path(f"videos/video_{number:02}.mp4")

    print(f"Creating video {number}: {title}")

    gTTS(text=spoken_text, lang="en").save(str(audio))
    duration = get_duration(audio)

    make_subtitles(spoken_text, duration, subtitles)

    found = get_pixabay_video(
        item["visual_search"], background
    )

    subtitle_filter = (
        f"subtitles=filename='{subtitles.as_posix()}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,"
        "Outline=2,Shadow=1,Alignment=2,MarginV=180'"
    )

    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920," + subtitle_filter
    )

    if found:
        command = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(background),
            "-i", str(audio),
            "-vf", video_filter,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(duration),
        ]
    else:
        command = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=0x18202b:s=1080x1920:r=30",
            "-i", str(audio),
            "-vf", video_filter,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(duration),
        ]

    command += [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output)
    ]

    subprocess.run(command, check=True)

    return output

# Save scripts and captions
report = ["DAILY TIKTOK CONTENT\n"]

for number, item in enumerate(items, 1):
    report.extend([
        f"\nVIDEO {number}: {item['title']}",
        f"Script: {item['hook']} {item['script']}",
        f"Caption: {item['caption']}",
        f"Hashtags: {item['hashtags']}",
        ""
    ])

Path("content/daily_videos.txt").write_text(
    "\n".join(report), encoding="utf-8"
)

# Render all 9 videos
for number, item in enumerate(items, 1):
    render_video(item, number)
    time.sleep(2)

print("SUCCESS: All 9 TikTok MP4 videos created!")
