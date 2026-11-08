import os
from pathlib import Path
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Create exactly 9 original TikTok video concepts
for a mixed viral entertainment account.

Include a variety of:
- Interesting facts
- Life hacks
- Funny moments
- Motivation
- Technology
- Animals
- Amazing discoveries
- Storytelling
- Trending video formats

For each video provide:
1. Catchy opening hook
2. 20-30 second script
3. Scene-by-scene visual instructions
4. On-screen text
5. Voiceover
6. Caption
7. Hashtags

Make all 9 videos different.
Use engaging, natural English.
Avoid fake facts and copyrighted footage.
"""

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt
)

output = response.text

Path("content").mkdir(exist_ok=True)
Path("content/daily_videos.txt").write_text(
    output,
    encoding="utf-8"
)

print("Successfully generated 9 TikTok video scripts!")
