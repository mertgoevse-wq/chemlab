# ChemLab Asset Generation Pipeline

Complete asset generation pipeline for ChemLab using Google AI Pro (Nano Banana, Veo, Flow Music).

## Overview

This pipeline generates all game assets at build time using Google AI Pro models:

| Tool | Model | Purpose |
|------|-------|---------|
| `nano_banana_generate.py` | Nano Banana Pro / 2 | Lab environments, equipment icons, character portraits |
| `veo_generate.py` | Veo 2 | Cinematic videos (loading, transitions, story beats) |
| `flow_music_generate.py` | Suno / UDIO | Ambient music, reaction sounds, UI sounds |
| `google_oauth.py` | Service Account | Authentication & rate limiting |
| `import_assets.py` | FFmpeg/Pillow | Format conversion & manifest management |

## Prerequisites

1. **Google AI Pro subscription** (Mert.govse.neu@gmail.com)
2. **Google Cloud Project** with AI Platform API enabled
3. **Service Account** with roles:
   - `AI Platform User`
   - `Vertex AI User`
   - `Cloud Storage User` (if using GDrive)
4. **Service Account Key** (JSON) downloaded locally

### Python Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 requests
pip install pillow ffmpeg-python  # For import pipeline
```

System dependencies: `ffmpeg` (for video/audio conversion)

## Quick Start

### 1. Setup Authentication

```bash
# Run interactive setup wizard
python tools/asset_pipeline/google_oauth.py --setup
```

This will:
- Prompt for your service account JSON key
- Save credentials to `.credentials/service_account.json`
- Test authentication
- Create config file

### 2. Generate Assets (Dry Run First)

```bash
# Preview all prompts without generating
python tools/asset_pipeline/nano_banana_generate.py --mode all --dry-run
python tools/asset_pipeline/veo_generate.py --mode all --dry-run
python tools/asset_pipeline/flow_music_generate.py --mode all --dry-run
```

### 3. Generate Assets (Using Browser Bridge)

If you don't have API keys yet, use the browser bridge (requires signed-in Chrome session):

```bash
# First, sign in once
python tools/google_bridge.py --login

# Then generate images via bridge
python tools/asset_pipeline/nano_banana_generate.py --mode environments --bridge
python tools/asset_pipeline/nano_banana_generate.py --mode equipment --bridge
python tools/asset_pipeline/nano_banana_generate.py --mode characters --bridge
```

### 4. Generate Assets (Using API Keys)

When you have API keys from [AI Studio](https://aistudio.google.com/apikey):

```bash
export GEMINI_API_KEY=your_key_here

# Generate all Nano Banana assets
python tools/asset_pipeline/nano_banana_generate.py --mode all

# Generate Veo videos (requires Veo API access)
python tools/asset_pipeline/veo_generate.py --mode all

# Generate audio (requires Suno/UDIO API)
export SUNO_API_KEY=your_key_here
python tools/asset_pipeline/flow_music_generate.py --mode all
```

### 5. Import & Convert Assets

If you downloaded assets manually or from Google Drive:

```bash
# Import from local directory
python tools/asset_pipeline/import_assets.py --source local --path ./downloaded_assets

# Import using manifest
python tools/asset_pipeline/import_assets.py --source manifest --manifest ./asset_manifest.json
```

This will:
- Convert images to PNG/WebP + generate thumbnails
- Convert videos to WebM (VP9) + MP4 (H.264)
- Convert audio to OGG (Vorbis) + MP3
- Update `game/data/media/manifest.json`

## Detailed Usage

### Nano Banana Generation

```bash
# Specific modes
python tools/asset_pipeline/nano_banana_generate.py --mode environments
python tools/asset_pipeline/nano_banana_generate.py --mode equipment
python tools/asset_pipeline/nano_banana_generate.py --mode characters

# Limit for testing
python tools/asset_pipeline/nano_banana_generate.py --mode all --limit 5

# Resume interrupted generation
python tools/asset_pipeline/nano_banana_generate.py --mode all --resume
```

**Outputs:**
- Environments: `game/assets/environments/*.png` (16:9, 2048px max)
- Equipment: `game/assets/equipment/*.png` (1:1, 512px max)
- Characters: `game/assets/characters/*.png` (3:4, 1024px max)

### Veo Video Generation

```bash
# Loading screen loops
python tools/asset_pipeline/veo_generate.py --mode loading

# Transitions
python tools/asset_pipeline/veo_generate.py --mode transition

# Story beats
python tools/asset_pipeline/veo_generate.py --mode story
```

**Outputs:**
- Videos: `game/assets/video/*.webm` (VP9) + `*.mp4` (H.264 fallback)
- Max resolution: 1920x1080

### Flow Music / Audio Generation

```bash
# Ambient lab soundscapes
python tools/asset_pipeline/flow_music_generate.py --mode ambient

# Reaction sounds
python tools/asset_pipeline/flow_music_generate.py --mode reactions

# UI sounds
python tools/asset_pipeline/flow_music_generate.py --mode ui
```

**Outputs:**
- Audio: `game/assets/audio/**/*.ogg` (Vorbis) + `*.mp3` + `*.wav`
- Sample rate: 48kHz, -18 LUFS target

### Import Pipeline

```bash
# From local folder
python tools/asset_pipeline/import_assets.py --source local --path ./my_assets --dest game/assets

# With manifest file
python tools/asset_pipeline/import_assets.py --source manifest --manifest ./import_manifest.json

# Dry run
python tools/asset_pipeline/import_assets.py --source local --path ./my_assets --dry-run
```

## Asset Manifest

The pipeline maintains `game/data/media/manifest.json` with:
- Asset metadata (ID, name, category, paths)
- Provenance (prompt, model, generation timestamp)
- Format variants (primary + fallbacks)
- Thumbnails
- SHA256 hashes for integrity

## Godot Integration

Assets are organized for direct Godot 4+ consumption:

```
game/assets/
├── environments/     # Lab backgrounds (Texture2D)
├── equipment/        # Apparatus icons (Texture2D)
├── characters/       # Portraits (Texture2D)
├── video/            # Cinematics (VideoStream)
├── audio/
│   ├── ambient/      # Looping ambiences (AudioStreamOGGVorbis)
│   ├── reactions/    # One-shot effects (AudioStreamOGGVorbis)
│   └── ui/           # UI sounds (AudioStreamOGGVorbis)
└── models/           # 3D models (GLB)
```

### Loading in Godot

```gdscript
# Texture
var lab_tex := load("res://assets/environments/analytical_lab.png") as Texture2D

# Video
var video_player := VideoStreamPlayer.new()
video_player.stream = load("res://assets/video/loading_lab_night.webm") as VideoStream

# Audio
var ambience := AudioStreamPlayer.new()
ambience.stream = load("res://assets/audio/ambient/ambient_analytical_lab.ogg") as AudioStream
```

## Rate Limits & Best Practices

The pipeline enforces Google AI Pro rate limits:

| Model | Requests/Min | Requests/Day |
|-------|--------------|--------------|
| Nano Banana (flash) | 60 | 1,000 |
| Nano Banana Pro | 30 | 500 |
| Veo 2 | 10 | 100 |
| Flow Music | 20 | 200 |

**Tips:**
- Use `--resume` to continue interrupted generations
- Run generations in batches with delays
- Monitor with `python tools/asset_pipeline/google_oauth.py --status`
- Use `--dry-run` to validate prompts before spending quota

## Troubleshooting

### "No API key provided"
```bash
export GEMINI_API_KEY=your_key
# or
python tools/asset_pipeline/nano_banana_generate.py --bridge
```

### "Service account not found"
```bash
python tools/asset_pipeline/google_oauth.py --setup
```

### "Rate limit exceeded"
```bash
# Check status
python tools/asset_pipeline/google_oauth.py --status

# Wait for reset
python tools/asset_pipeline/google_oauth.py --wait-rate-limit nano-banana-pro
```

### "ffmpeg not found"
```bash
# Windows: Download from ffmpeg.org, add to PATH
# Or: winget install ffmpeg
# Linux: apt install ffmpeg
# Mac: brew install ffmpeg
```

### "PIL/Pillow not installed"
```bash
pip install pillow
```

## File Structure

```
tools/asset_pipeline/
├── nano_banana_generate.py   # Image generation (15 labs, 50+ equipment, 26 chars + 8 animals)
├── veo_generate.py           # Video generation (5 loading, 3 transitions, 10 story)
├── flow_music_generate.py    # Audio generation (20 ambient, 20 reactions, 20 UI)
├── google_oauth.py           # Auth, token refresh, rate limiting
├── import_assets.py          # Format conversion & manifest
└── asset_manifest.json       # Pipeline config (copied to game/data/media/)

game/data/media/
└── manifest.json             # Runtime asset manifest

.credentials/
├── service_account.json      # Service account key (gitignored)
├── token_cache.json          # Cached access tokens
├── oauth_config.json         # Pipeline config
└── rate_limit_*.json         # Per-model rate limit state
```

## Credits & Attribution

- **Nano Banana**: Google AI Pro image generation
- **Veo**: Google AI Pro video generation  
- **Flow Music**: Suno / UDIO audio generation
- **Prompts**: Custom-designed for ChemLab's scientific aesthetic
- **Pipeline**: Built for Athanor Ascension / ChemLab project

## License

Generated assets are for use in ChemLab only. Prompts and pipeline code are proprietary.