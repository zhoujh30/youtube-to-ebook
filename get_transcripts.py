"""
Part 2: Extract Transcripts from YouTube Videos
Uses youtube-transcript-api to fetch transcripts for free.
Caches transcripts locally to avoid re-fetching.
"""

import os
import json
import time
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


_api = YouTubeTranscriptApi()
_CACHE_FILE = os.path.join(os.path.dirname(__file__), "transcript_cache.json")


def _load_cache():
    if os.path.exists(_CACHE_FILE):
        with open(_CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    with open(_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def get_transcript(video_id):
    """
    Get the transcript for a YouTube video using youtube-transcript-api (free, no API key needed).
    Returns the full text, or None if unavailable.
    """
    cache = _load_cache()
    if video_id in cache:
        print(f"  ✓ Loaded from cache")
        return cache[video_id]

    try:
        transcript_list = _api.fetch(video_id)
        full_text = " ".join(t.text for t in transcript_list)
        result = full_text.strip()
        cache[video_id] = result
        _save_cache(cache)
        return result
    except TranscriptsDisabled:
        print(f"  ⚠ Transcripts disabled for this video")
        return None
    except NoTranscriptFound:
        print(f"  ⚠ No transcript available for this video")
        return None
    except Exception as e:
        print(f"  ⚠ Error getting transcript: {e}")
        return None


def get_transcripts_for_videos(videos):
    """
    Get transcripts for a list of videos.
    Takes the video list from get_videos.py and adds transcripts.
    """
    print("\nExtracting transcripts via Supadata API...\n")
    print("=" * 60)

    for i, video in enumerate(videos):
        print(f"Getting transcript: {video['title'][:50]}...")

        transcript = get_transcript(video["video_id"])

        if transcript:
            video["transcript"] = transcript
            word_count = len(transcript.split())
            print(f"  ✓ Got {word_count} words\n")
        else:
            video["transcript"] = None
            print(f"  ✗ No transcript available\n")

        # Small delay between requests to be nice to the API
        if i < len(videos) - 1:
            time.sleep(1)

    # Filter out videos without transcripts
    videos_with_transcripts = [v for v in videos if v.get("transcript")]

    print("=" * 60)
    print(f"Got transcripts for {len(videos_with_transcripts)} of {len(videos)} videos")

    return videos_with_transcripts


# Test it standalone
if __name__ == "__main__":
    # Test with a sample video
    test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    print("Testing Supadata transcript extraction...")
    print(f"API Key configured: {'Yes' if SUPADATA_API_KEY and SUPADATA_API_KEY != 'your_supadata_api_key_here' else 'No'}")
    transcript = get_transcript(test_video_id)
    if transcript:
        print(f"Got transcript! First 200 chars:\n{transcript[:200]}...")
    else:
        print("Failed to get transcript")
