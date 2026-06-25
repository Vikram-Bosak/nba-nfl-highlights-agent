# 🏀🏈 NBA/NFL Highlights Agent

Automated pipeline that monitors NBA and NFL social media accounts for the latest highlights, edits them into engaging Facebook Reels and YouTube Shorts, and uploads them automatically.

## How It Works

The pipeline runs every 3 hours and follows this sequence:

1. **Download** → Scans 10 NBA/NFL Twitter profiles via Nitter RSS for new video tweets (last 3 hours)
2. **Edit** → Applies professional editing: 3:4 ratio (1080x1440) for Facebook Reels, color grading, zoom effects, audio boost, and custom UI frame with AI-generated headlines
3. **Upload** → Posts to Facebook Reels and YouTube Shorts (gracefully skips if no API keys configured)

## Features

- **Nitter RSS scraping** (no Playwright needed) for reliable Twitter video detection
- **AI-powered headlines** via NVIDIA LLM API for viral-optimized content
- **Deep video analysis** via Google Gemini (optional) for better context
- **Daily limits** (5 downloads, 5 edits, 5 uploads per day)
- **Telegram notifications** for every pipeline stage
- **GitHub Actions** for fully automated scheduling
- **History tracking** to prevent duplicate processing
- **Graceful degradation** — works without Facebook/YouTube API keys (just skips upload)

## Monitored Profiles

| Profile | Sport |
|---------|-------|
| @SportsCenter | Both |
| @BleacherReport | Both |
| @NBA | NBA |
| @NFL | NFL |
| @ShamsCharania | NBA |
| @AdamSchefter | NFL |
| @ESPN | Both |
| @BleacherReport | Both |
| @NBA | NBA |
| @NFL | NFL |

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/nba-nfl-highlights-agent.git
cd nba-nfl-highlights-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run Locally

```bash
python main_agent.py
```

### 5. Deploy on GitHub Actions

1. Push to GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add the following secrets (all optional):
   - `TELEGRAM_BOT_TOKEN` - Telegram bot token for notifications
   - `TELEGRAM_CHAT_ID` - Telegram chat ID for notifications
   - `FB_ACCESS_TOKEN` - Facebook Graph API access token
   - `FB_PAGE_ID` - Facebook Page ID
   - `YOUTUBE_TOKEN_JSON` - YouTube API token JSON
   - `NVIDIA_API_KEY` - NVIDIA API key for AI headlines
   - `GEMINI_API_KEY` - Google Gemini API key for video analysis
4. The pipeline runs automatically every 3 hours via GitHub Actions

## Adding API Keys Later

The agent works perfectly without any API keys — it just won't upload to Facebook/YouTube and will use fallback headlines. To enable uploads:

1. **Facebook**: Create a Facebook App, get a Page Access Token, and set `FB_ACCESS_TOKEN` and `FB_PAGE_ID`
2. **YouTube**: Set up YouTube Data API v3 credentials and set `YOUTUBE_TOKEN_JSON`
3. **NVIDIA AI**: Get an API key from build.nvidia.com and set `NVIDIA_API_KEY`

## Project Structure

```
nba-nfl-highlights-agent/
├── main_agent.py              # Main pipeline orchestrator
├── src/
│   ├── agent_1_downloader.py  # Twitter/Nitter RSS video downloader
│   ├── agent_2_editor.py      # Video editor wrapper
│   ├── agent_3_uploader.py    # Facebook & YouTube uploader
│   ├── facebook_uploader.py   # Facebook Graph API client
│   ├── youtube_uploader.py    # YouTube Data API client
│   ├── logger.py              # Logging configuration
│   └── common/
│       ├── telegram.py        # Telegram bot notifications
│       ├── seo_generator.py   # AI headline & SEO generation
│       ├── limits.py          # Daily rate limiting
│       └── ui_frame_generator.py  # Custom UI frame for Reels
├── editor/
│   └── advanced_editor.py     # FFmpeg video editing (3:4 ratio)
├── assets/                    # Static assets (logos, banners)
├── workspace/                 # Temporary working directory
├── temp/                      # State and limits tracking
├── .github/workflows/
│   └── pipeline.yml           # GitHub Actions workflow
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

## License

MIT
