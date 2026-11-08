import os
from pathlib import Path
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Create exactly 9 original TikTok video concepts for my account.

Topics:
- Fitness and activewear
- Affiliate marketing
- Brand ambassador opportunities
- Finding customers on TikTok

For each video provide:
1. Catchy hook
2. 15-30 second script
3. Shot-by-shot filming instructions
4. On-screen text
5. Caption with CTA
6. Relevant hashtags

Use simple, natural English.
Make every video different.
Do not invent product claims or fake testimonials.
"""

response = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt
)

output = response.output_text

Path("content").mkdir(exist_ok=True)
Path("content/daily_videos.txt").write_text(
    output,
    encoding="utf-8"
)

print("Successfully generated 9 TikTok video scripts!")
