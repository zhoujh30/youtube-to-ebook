"""
Part 3: Transform Transcripts into Magazine Articles using Claude AI
Takes raw video transcripts and turns them into polished, readable articles.
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load your API key
load_dotenv()

# Create the Groq client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


MAX_TRANSCRIPT_WORDS = 8000


def write_article(video):
    """
    Use Claude to transform a video transcript into a magazine-style article.
    """
    transcript = video['transcript']
    words = transcript.split()
    if len(words) > MAX_TRANSCRIPT_WORDS:
        transcript = " ".join(words[:MAX_TRANSCRIPT_WORDS])
        print(f"  ℹ Transcript truncated to {MAX_TRANSCRIPT_WORDS} words (original: {len(words)})")

    prompt = f"""You are a reporter for The Information, a premium technology and business publication known for source-driven, precise, and strategically framed journalism. Transform this YouTube transcript into an article in The Information's signature style.

VIDEO TITLE: {video['title']}
CHANNEL: {video['channel']}
VIDEO URL: {video['url']}

VIDEO DESCRIPTION:
{video['description']}

TRANSCRIPT:
{transcript}

---

Write this as a The Information-style article. Requirements:

STRUCTURE:
- Start with a sharp headline (not the video title)
- Opening paragraph: 2-3 sentences synthesizing the single most important insight — a standalone executive summary
- Each subsequent paragraph must open with a **bold sentence** (using **double asterisks**) stating the key point. A reader scanning only the bold sentences should understand the full story.

VOICE & STYLE:
- Business and strategic angle: what are the competitive, financial, or industry implications?
- Cold precision: concrete facts and numbers over adjectives and hype
- Source-driven language: attribute insights naturally ("According to...", "People familiar with the matter say...", "X has told associates...")
- Correct transcription errors using the title and description (names of people, companies, products)
- Preserve key quotes — clean up filler words but keep the substance

WHAT TO AVOID:
- Never write "In this video", "the speaker says", or "in this conversation"
- No filler phrases or hype adjectives
- Do not summarize chronologically — synthesize thematically

Format in clean markdown. Bold the first sentence of every paragraph with **double asterisks**."""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                wait = 90 * (attempt + 1)
                print(f"  ⏳ Rate limit hit, waiting {wait}s before retry ({attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"  ⚠ Error generating article: {e}")
                return None

    print(f"  ⚠ Failed after 3 retries")
    return None


def write_articles_for_videos(videos):
    """
    Generate articles for all videos with transcripts.
    """
    print("\nGenerating articles with Claude AI...\n")
    print("=" * 60)

    articles = []

    for video in videos:
        print(f"Writing article: {video['title'][:50]}...")

        article = write_article(video)

        if article:
            articles.append({
                "title": video["title"],
                "channel": video["channel"],
                "url": video["url"],
                "video_id": video["video_id"],
                "article": article
            })
            print(f"  ✓ Article generated!\n")
        else:
            print(f"  ✗ Failed to generate article\n")

    print("=" * 60)
    print(f"Generated {len(articles)} articles")

    return articles


# Test it standalone
if __name__ == "__main__":
    # Test with a mock video
    test_video = {
        "title": "Test Video",
        "channel": "Test Channel",
        "url": "https://youtube.com/watch?v=test",
        "transcript": "Hello everyone, today we're going to talk about something really exciting. I've been working on this project for months and I can't wait to share it with you. The main idea is simple but powerful..."
    }

    print("Testing article generation...")
    article = write_article(test_video)
    if article:
        print("\nGenerated article:\n")
        print(article)
