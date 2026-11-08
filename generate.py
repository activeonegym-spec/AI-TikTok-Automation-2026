
import os
import time
import requests
from pathlib import Path
from google import genai

# Check API keys
gemini_key = os.environ.get("GEMINI_API_KEY")
pixabay_key = os.environ.get("PIXABAY_API_KEY")

if not gemini_key:
    raise ValueError("GEMINI_API_KEY is missing in GitHub Secrets.")

client = genai.Client(api_key=gemini_key)

# Generate exactly 9 TikTok video scripts
prompt = """
Create exactly 9 original, engaging TikTok video scripts
for a mixed viral entertainment account.

Include these topics:
1. Interesting facts
2. Life hacks
3. Funny moments
4. Motivation
5. Technology
6. Animals
7. Amazing discoveries
8. Short storytelling
9. Viral-style entertainment

For EACH video include:
- Catchy opening hook
- 20-30 second voiceover script
- Scene-by-scene visual instructions
- On-screen captions
- Video caption
- Relevant hashtags

Requirements:
- Make all 9 videos different.
- Use natural, engaging English.
- Use accurate facts. Do not invent statistics.
- Avoid copyrighted characters, music and footage.
- Make the scripts suitable for faceless videos.
"""

models = [
    "gemini-3.8-flash",
    "gemini-flash-latest"
]

output = None

# Retry if Gemini is temporarily unavailable
for model in models:
    for attempt in range(3):
        try:
            print(f"Trying {model}, attempt {attempt + 1}...")

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if response.text and response.text.strip():
                output = response.text.strip()
                print(f"Success using {model}")
                break

            raise ValueError("Gemini returned an empty response.")

        except Exception as error:
            print(f"Attempt failed: {error}")

            if attempt < 2:
                wait_time = 2 ** (attempt + 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    if output:
        break

if not output:
    raise RuntimeError(
        "Gemini could not generate scripts. "
        "Please check the API key, model availability and quota."
    )

# Create content folder and save scripts
Path("content").mkdir(exist_ok=True)

content = "# DAILY TIKTOK VIDEO SCRIPTS\n\n"
content += output

# Pixabay search is optional
if pixabay_key:
    try:
        print("Connecting to Pixabay...")

        pixabay_response = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": pixabay_key,
                "q": "nature",
                "per_page": 3
            },
            timeout=30
        )

        pixabay_response.raise_for_status()
        videos = pixabay_response.json().get("hits", [])

        content += "\n\n# PIXABAY STOCK VIDEO REFERENCES\n"

        for index, video in enumerate(videos, 1):
            video_files = video.get("videos", {})
            medium = video_files.get("medium", {})
            video_url = medium.get("url")

            if video_url:
                content += f"\nVideo {index}: {video_url}\n"

        print(f"Pixabay found {len(videos)} clips.")

    except Exception as error:
        print(f"Pixabay unavailable. Continuing: {error}")

else:
    print("Pixabay key not found. Skipping stock video search.")

Path("content/daily_videos.txt").write_text(
    content,
    encoding="utf-8"
)

print("SUCCESS: Daily TikTok scripts saved!")
