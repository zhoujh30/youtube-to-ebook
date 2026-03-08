# YouTube to Ebook — Daily AI Digest

> **This is a fork of [zarazhangrui/youtube-to-ebook](https://github.com/zarazhangrui/youtube-to-ebook).**
> The original project is a great foundation. This fork re-orients it toward a specific use case: a zero-cost, fully automated daily digest of AI-related YouTube content, delivered as a newsletter to your inbox every morning.

---

## What this does

Monitors a curated list of AI/tech YouTube channels every day. For any new video that passes quality filters, it extracts the transcript, rewrites it as a structured article, and emails you a newsletter — no manual work required.

---

## Changes from the original

### 1. Fully free API stack

The original uses paid APIs (Anthropic Claude for writing, Supadata for transcripts). This fork replaces both with free alternatives:

- **Gemini 3 Flash** instead of Anthropic Claude — free tier, better writing quality than the previous Groq/llama setup
- **youtube-transcript-api** (open source Python library, no key needed) instead of Supadata — pulls transcripts directly from YouTube's own subtitles

The only API that still requires a key is the YouTube Data API v3, which has a free daily quota of 10,000 units — more than enough for 14 channels.

### 2. Daily cadence instead of weekly

Weekly digests tend to pile up and go unread. This fork runs every morning at 9 AM (London time) via GitHub Actions — no computer needed, fully cloud-based. If there's nothing new that day, no email is sent.

### 3. No content pre-filter (all qualifying videos processed)

All videos that pass the quality filters (duration, views, captions) are processed into articles. There is intentionally no keyword pre-filter — title-only filtering misses too many relevant videos (e.g. Lex Fridman interviewing an AI researcher where the title is just the person's name), and description-based filtering causes false positives from sponsor text. Channel curation is the main signal for relevance.

### 4. The Information–style articles

The original prompt produces a general summary. This fork rewrites the prompt to produce articles in the style of *The Information* — a premium tech business publication:

- Opens with a 2–3 sentence executive summary of the single most important insight
- Each paragraph's first sentence is bolded, so the key points are scannable
- Business and strategic framing: competitive implications, not just "what was said"
- Attribute insights naturally, clean up transcript filler words, correct misspelled names using the video description

### 5. Redesigned email newsletter

The original email is functional but plain. This fork redesigns it as a clean, readable newsletter:

- Georgia serif font at 20px — optimised for reading, not scanning
- Light background, black text — no dark mode that strains reading
- YouTube thumbnail pulled automatically (free CDN, no API call)
- Guest/speaker name extracted from video title and shown as a byline
- Mobile-responsive layout

### 6. Stricter video quality filters

To keep the digest high-signal:

- Duration > 20 minutes (filters out shorts, quick takes, clips)
- View count > 1,000 (new videos have a grace period — this is a light filter)
- Must have captions available (required for transcript extraction)

### 7. Curated channel list

14 channels covering AI research, industry news, startup/VC perspective, and long-form interviews:

```
@DwarkeshPatel, @AndrejKarpathy, @lexfridman, @AIDailyBrief,
@LennysPodcast, @aiDotEngineer, @OpenAI, @ycombinator,
@GoogleDeepMind, @MicrosoftResearch, @a16z, @GarryTan,
@20VC, @MachineLearningStreetTalk
```

Edit `channels.txt` to add or remove channels.

---

## Setup

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/youtube-to-ebook.git
cd youtube-to-ebook
pip install -r requirements.txt
```

### 2. Get API keys (all free)

**YouTube Data API v3**
1. [Google Cloud Console](https://console.cloud.google.com/) → Create project
2. Enable "YouTube Data API v3" → Create API Key

**Gemini API**
1. [aistudio.google.com](https://aistudio.google.com) → Sign in → Get API Key
2. Free tier: sufficient for personal daily use

**Gmail App Password**
1. Enable 2FA on your Google account
2. Google Account → Security → App Passwords → Generate

### 3. Configure `.env`

```bash
cp .env.example .env
```

```
YOUTUBE_API_KEY=your_key
GEMINI_API_KEY=your_key
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 4. Set up GitHub Actions (automated daily run)

1. Push this repo to your GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add the 4 secrets above (`YOUTUBE_API_KEY`, `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`)
4. The workflow runs automatically at 9 AM UTC (London time) every day
5. To trigger manually: Actions tab → "Daily YouTube Digest" → Run workflow

### 5. Run locally (optional)

```bash
python main.py
```

---

## Project structure

```
├── main.py              # Pipeline orchestrator + AI content filter
├── get_videos.py        # Fetch and quality-filter recent videos
├── get_transcripts.py   # Extract transcripts via youtube-transcript-api
├── write_articles.py    # Rewrite transcripts as articles via Groq
├── send_email.py        # Generate HTML newsletter + EPUB, send via Gmail
├── video_tracker.py     # Deduplication — avoids re-sending processed videos
├── channels.txt         # Channel list (one handle per line)
├── .env                 # API keys (not committed)
└── newsletters/         # Local archive of sent newsletters
```

---

## License

The original project does not include a license file. This fork is shared for personal and educational use. If you build on this, please credit both [zarazhangrui](https://github.com/zarazhangrui/youtube-to-ebook) and this fork.
