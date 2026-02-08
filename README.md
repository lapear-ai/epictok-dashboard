# EpicTok Dashboard

Fully automated historical video generator with web dashboard.

## 🚀 Quick Start

```bash
cd tools/epictok-dashboard
./start.sh
```

Then open: **http://localhost:8766**

## ✨ Features

- **One-Click Video Generation** - Fetches history, writes script, generates image, voiceover, and video
- **Background Processing** - Queue multiple jobs, they process automatically
- **Real-Time Progress** - Watch generation status live
- **Video Library** - Download completed videos
- **Statistics Dashboard** - Track total/completed/pending videos

## 🎯 How It Works

1. Click **"Generate Video"** on dashboard
2. System automatically:
   - Fetches random historical event from Wikipedia
   - Generates engaging script with viral hooks
   - Creates AI image using Pollinations (free)
   - Generates voiceover using ElevenLabs
   - Assembles video with Ken Burns effect
3. Download and upload to TikTok/YouTube/Instagram

## 🔧 Configuration

Set environment variables for full automation:

```bash
export ELEVENLABS_API_KEY="your_key_here"
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"  # Optional
```

Or add to `~/.zshrc` for persistence.

## 📁 File Structure

```
epictok-dashboard/
├── app.py                 # Flask backend
├── templates/
│   └── dashboard.html     # Web interface
├── requirements.txt       # Dependencies
├── start.sh              # Launch script
└── output/               # Generated videos
    └── 20260207_190010_Project_Name/
        ├── metadata.json
        ├── script.txt
        ├── scene.jpg     # AI image
        ├── voiceover.mp3 # ElevenLabs audio
        └── final_video.mp4
```

## 🎬 Batch Generation

Generate 10 videos at once:

```bash
for i in {1..10}; do
  curl -X POST http://localhost:8766/api/generate
done
```

Or use the web dashboard to queue multiple jobs.

## 🔄 Automation

### Daily Auto-Generation

Add to crontab:

```bash
# Generate 3 videos daily at 9 AM
0 9 * * * cd /path/to/epictok-dashboard && python3 -c "
import requests
for i in range(3):
    requests.post('http://localhost:8766/api/generate')
"
```

### Auto-Upload (Advanced)

For full automation including social media upload, extend `app.py` with:
- YouTube Data API
- TikTok API (via unofficial clients)
- Instagram Graph API

## 💰 Monetization

1. **YouTube Partner Program** - Upload longer versions (8+ min)
2. **TikTok Creator Fund** - Short-form vertical videos
3. **Affiliate Marketing** - History books, documentaries
4. **Sponsorships** - Museum apps, educational platforms

## 🎨 Customization

Edit `app.py` to customize:

- **Historical topics** - Line 25: `HISTORY_TOPICS` list
- **Script style** - Line 99: `generate_script()` function
- **Video effects** - Line 216: FFmpeg command
- **Image style** - Line 118: `generate_image_prompt()`

## 📊 Dashboard

The web interface shows:
- Real-time job progress
- Project library with download buttons
- Statistics: Total Projects / Videos / Pending
- Status tags for each asset (Image/Voice/Video)

## 🐛 Troubleshooting

**Port already in use:**
```bash
lsof -i :8766  # Find process
kill -9 <PID>  # Kill it
```

**Missing FFmpeg:**
```bash
brew install ffmpeg
```

**ElevenLabs API errors:**
- Check API key is valid
- Verify account has credits
- Check voice ID exists

## 📝 Requirements

- Python 3.8+
- Flask
- FFmpeg
- ElevenLabs API key (for voice)
- Internet connection

## 🎉 Next Steps

1. Start the dashboard
2. Generate your first video
3. Download and review
4. Upload to social media
5. Build audience
6. Monetize

---

**Built for Larren Peart | EpicTok Historical Video Factory**
