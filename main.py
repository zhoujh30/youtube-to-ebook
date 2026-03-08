"""
YouTube Newsletter Generator - Main Script
Ties together all the pieces: fetch videos → get transcripts → write articles → send email
Tracks processed videos to avoid sending duplicates.
"""

import re

from get_videos import main as fetch_videos
from get_transcripts import get_transcripts_for_videos
from write_articles import write_articles_for_videos
from send_email import send_newsletter
from video_tracker import filter_new_videos, mark_videos_processed, get_processed_count

# AI filter: checked against TITLE ONLY (descriptions often contain sponsor
# text with unrelated AI mentions, e.g. "ML internship" in a history video).
# Uses word-boundary regex for short terms to avoid substring false positives.
_AI_KEYWORDS = [
    # Unambiguous short terms — need word boundaries
    r"\bai\b", r"\bagi\b", r"\bllm\b", r"\bllms\b",
    r"\brlhf\b", r"\bgpt\b", r"\bxai\b",
    # Multi-word concepts — specific enough for plain substring match
    "artificial intelligence", "machine learning", "deep learning",
    "large language model", "foundation model", "language model",
    "neural network", "reinforcement learning", "multimodal",
    "superintelligence", "alignment",
    # Model / product names
    "chatgpt", "openai", "anthropic", "deepmind",
    r"\bclaude\b", r"\bgemini\b", r"\bllama\b", r"\bmistral\b", r"\bgrok\b",
    # Companies
    "meta ai", "google deepmind", "hugging face", r"\bnvidia\b",
    # Key people
    "sam altman", "dario amodei", "andrej karpathy", "ilya sutskever",
    "jensen huang", "demis hassabis", "yann lecun", "greg brockman",
]


def is_ai_related(video):
    # Check title only — descriptions contain sponsor text that causes false positives
    title = video.get("title", "").lower()
    for kw in _AI_KEYWORDS:
        if kw.startswith(r"\b") or kw.endswith(r"\b"):
            if re.search(kw, title):
                return True
        else:
            if kw in title:
                return True
    return False


def filter_ai_videos(videos):
    ai_videos = [v for v in videos if is_ai_related(v)]
    skipped = len(videos) - len(ai_videos)
    if skipped:
        print(f"  ✗ Skipped {skipped} non-AI video(s):")
        for v in videos:
            if not is_ai_related(v):
                print(f"    - {v['title'][:60]}")
    print(f"  → {len(ai_videos)} AI-related video(s) to process")
    return ai_videos


def run():
    """
    Run the full newsletter pipeline.
    """
    print("=" * 60)
    print("  YOUTUBE NEWSLETTER GENERATOR")
    print("=" * 60)
    print(f"  Previously processed: {get_processed_count()} videos")

    # Step 1: Fetch latest videos from your channels
    print("\n📺 STEP 1: Fetching latest videos...\n")
    videos = fetch_videos()

    if not videos:
        print("No videos found. Check your channel list.")
        return

    # Step 1b: Filter out already-processed videos
    print("\n🔍 Checking for new videos...\n")
    new_videos = filter_new_videos(videos)

    if not new_videos:
        print("No new videos to process. All videos have been sent before.")
        print("=" * 60)
        return

    print(f"\n  → {len(new_videos)} new video(s) to process\n")

    # Step 1c: Pre-filter for AI relevance (title/description check, no API cost)
    print("\n🤖 Filtering for AI-related videos...\n")
    ai_videos = filter_ai_videos(new_videos)

    if not ai_videos:
        print("\nNo AI-related videos found today.")
        print("=" * 60)
        return

    # Step 2: Get transcripts for those videos
    print("\n📝 STEP 2: Extracting transcripts...\n")
    videos_with_transcripts = get_transcripts_for_videos(ai_videos)

    if not videos_with_transcripts:
        print("No transcripts available for any videos.")
        return

    # Step 3: Generate articles using Groq AI
    print("\n✍️ STEP 3: Writing articles with Groq AI...\n")
    articles = write_articles_for_videos(videos_with_transcripts)

    if not articles:
        print("No articles generated.")
        return

    # Step 4: Send the newsletter via email
    print("\n📧 STEP 4: Sending newsletter...\n")
    success = send_newsletter(articles, recipient_email="zhoujh42@gmail.com")

    # Step 5: Mark videos as processed (only if email sent successfully)
    if success:
        mark_videos_processed(videos_with_transcripts)
        print(f"\n  ✓ Marked {len(videos_with_transcripts)} video(s) as processed")

    print("\n" + "=" * 60)
    print("  DONE!")
    print("=" * 60)

    return articles


if __name__ == "__main__":
    run()
