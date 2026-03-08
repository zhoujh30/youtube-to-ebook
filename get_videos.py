"""
Part 1: Fetch Latest Videos from YouTube Channels
Fetches videos from the past 24 hours, applies quality filters:
- Duration > 20 minutes (also filters out Shorts automatically)
- View count > 1,000
- Has captions available
"""

import os
import re
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

_channels_file = os.path.join(os.path.dirname(__file__), "channels.txt")
with open(_channels_file) as f:
    CHANNELS = [line.strip() for line in f if line.strip()]

ONE_DAY_AGO = datetime.now(timezone.utc) - timedelta(days=1)


def parse_duration_seconds(iso_duration):
    """
    Parse ISO 8601 duration (e.g. PT1H23M45S) into total seconds.
    """
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def get_channel_info(youtube, channel_handle):
    handle = channel_handle.lstrip("@")
    response = youtube.channels().list(
        part="snippet,contentDetails",
        forHandle=handle
    ).execute()

    if response.get("items"):
        channel = response["items"][0]
        return {
            "channel_id": channel["id"],
            "channel_name": channel["snippet"]["title"],
            "uploads_playlist_id": channel["contentDetails"]["relatedPlaylists"]["uploads"]
        }
    return None


def get_recent_video_ids(youtube, uploads_playlist_id):
    """
    Get video IDs published in the past 24 hours from a channel's uploads playlist.
    """
    response = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=10
    ).execute()

    video_ids = []
    for item in response.get("items", []):
        published_str = item["snippet"]["publishedAt"]
        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

        if published_at < ONE_DAY_AGO:
            break

        video_ids.append((
            item["snippet"]["resourceId"]["videoId"],
            item["snippet"]["title"],
            item["snippet"]["description"],
        ))

    return video_ids


def get_video_details(youtube, video_ids):
    """
    Batch-fetch video details (duration, views, captions) for a list of video IDs.
    Returns a dict keyed by video_id.
    """
    if not video_ids:
        return {}

    response = youtube.videos().list(
        part="contentDetails,statistics",
        id=",".join(video_ids)
    ).execute()

    details = {}
    for item in response.get("items", []):
        vid = item["id"]
        duration_sec = parse_duration_seconds(item["contentDetails"].get("duration", "PT0S"))
        view_count = int(item["statistics"].get("viewCount", 0))
        has_captions = item["contentDetails"].get("caption", "false") == "true"
        details[vid] = {
            "duration_sec": duration_sec,
            "view_count": view_count,
            "has_captions": has_captions,
        }
    return details


def get_recent_videos(youtube, uploads_playlist_id, channel_name):
    """
    Get quality-filtered videos published in the past 24 hours.
    Filters: duration > 20 min, views > 1k, has captions.
    """
    candidate_ids = get_recent_video_ids(youtube, uploads_playlist_id)
    if not candidate_ids:
        return []

    id_list = [vid for vid, _, _ in candidate_ids]
    details = get_video_details(youtube, id_list)

    recent_videos = []
    for video_id, title, description in candidate_ids:
        d = details.get(video_id, {})
        duration_sec = d.get("duration_sec", 0)
        view_count = d.get("view_count", 0)
        has_captions = d.get("has_captions", False)

        # Quality filters
        if duration_sec < 20 * 60:
            print(f"  ✗ Skipped (too short: {duration_sec//60}min): {title[:50]}")
            continue
        if view_count < 1000:
            print(f"  ✗ Skipped (low views: {view_count}): {title[:50]}")
            continue
        if not has_captions:
            print(f"  ✗ Skipped (no captions): {title[:50]}")
            continue

        recent_videos.append({
            "title": title,
            "video_id": video_id,
            "description": description,
            "channel": channel_name,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return recent_videos


def main():
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    print("Fetching videos from the past 24h (duration>20min, views>1k, has captions)...\n")
    print("=" * 60)

    videos = []

    for channel_handle in CHANNELS:
        print(f"Looking up: {channel_handle}")
        channel_info = get_channel_info(youtube, channel_handle)

        if channel_info:
            print(f"  Channel: {channel_info['channel_name']}")
            channel_videos = get_recent_videos(
                youtube,
                channel_info["uploads_playlist_id"],
                channel_info["channel_name"]
            )

            if channel_videos:
                for video in channel_videos:
                    videos.append(video)
                    print(f"  ✓ Found: {video['title']}")
                    print(f"    URL: {video['url']}")
                print()
            else:
                print(f"  ✗ No qualifying videos in the past 24h\n")
        else:
            print(f"  ✗ Channel not found\n")

    print("=" * 60)
    print(f"Found {len(videos)} videos total!")

    return videos


if __name__ == "__main__":
    main()
