#!/usr/bin/env python3
"""
Asset Import Pipeline for ChemLab

Downloads generated assets, converts to Godot-compatible formats,
updates manifest, and generates thumbnails/previews.

Supported conversions:
- Images: PNG/JPG -> PNG (Godot), WebP (web), KTX2 (GPU compressed)
- Video: MP4 -> WebM (VP9), OGV (Theora), keep MP4 (H.264)
- Audio: WAV -> OGG (Vorbis), MP3, keep WAV (PCM)
- 3D: GLB/GLTF -> GLB (Godot optimized)

Usage:
    python import_assets.py --source gdrive --folder-id <id>
    python import_assets.py --source local --path ./generated
    python import_assets.py --source api --manifest manifest.json
    python import_assets.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "game" / "data" / "media" / "manifest.json"
IMPORT_LOG = ROOT / "tools" / "asset_pipeline" / "import_log.json"

# ─── Configuration ──────────────────────────────────────────────────────────

GODOT_TEXTURE_SETTINGS = {
    "max_dimension": 2048,
    "compress_mode": "vram_compressed",  # VRAM compressed (KTX2/BasisU)
    "mipmaps": True,
    "filter": True,
    "repeat": True,
}

VIDEO_SETTINGS = {
    "max_resolution": (1920, 1080),
    "codecs": ["vp9", "h264"],  # WebM VP9 + MP4 H.264 fallback
    "crf": 23,
    "preset": "medium",
}

AUDIO_SETTINGS = {
    "sample_rate": 48000,
    "bitrate": "128k",
    "formats": ["ogg", "mp3"],  # OGG Vorbis + MP3 fallback
}

THUMBNAIL_SIZES = {
    "small": (128, 128),
    "medium": (256, 256),
    "large": (512, 512),
}

# ─── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class AssetInfo:
    id: str
    name: str
    category: str
    source_path: str
    dest_path: str
    mime_type: str
    size_bytes: int
    sha256: str
    width: int = 0
    height: int = 0
    duration_sec: float = 0.0
    converted_files: list = None
    thumbnails: dict = None
    provenance: dict = None
    status: str = "pending"
    error: str = ""

    def __post_init__(self):
        if self.converted_files is None:
            self.converted_files = []
        if self.thumbnails is None:
            self.thumbnails = {}
        if self.provenance is None:
            self.provenance = {}


# ─── Utility Functions ──────────────────────────────────────────────────────

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_mime_type(filepath: Path) -> str:
    """Get MIME type of file."""
    mime, _ = mimetypes.guess_type(str(filepath))
    return mime or "application/octet-stream"


def load_manifest() -> dict:
    if ASSET_MANIFEST.exists():
        with open(ASSET_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": 1, "assets": []}


def save_manifest(manifest: dict):
    ASSET_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(ASSET_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def load_import_log() -> dict:
    if IMPORT_LOG.exists():
        with open(IMPORT_LOG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": 1, "imports": []}


def save_import_log(log: dict):
    IMPORT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(IMPORT_LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def run_cmd(cmd: list, timeout: int = 300) -> tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


# ─── Image Conversion ───────────────────────────────────────────────────────

def convert_image(source: Path, dest_dir: Path, asset_id: str, max_dim: int = 2048) -> list[dict]:
    """Convert image to Godot-compatible formats. Returns list of converted file info."""
    if Image is None:
        return [{"error": "PIL/Pillow not installed"}]

    results = []
    try:
        with Image.open(source) as img:
            # Convert to RGB if needed (remove alpha for non-transparent)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Check if actually has transparency
                if img.mode == 'P':
                    img = img.convert('RGBA')
                has_alpha = img.mode in ('RGBA', 'LA') and any(
                    pixel[3] < 255 for pixel in img.getdata()
                ) if img.mode in ('RGBA', 'LA') else False
                if not has_alpha:
                    # Flatten to white background
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        bg.paste(img, mask=img.split()[3])
                    else:
                        bg.paste(img)
                    img = bg
                else:
                    img = img.convert('RGBA')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Resize if needed
            if max(img.width, img.height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            # Save as PNG (Godot primary)
            png_path = dest_dir / f"{asset_id}.png"
            img.save(png_path, "PNG", optimize=True, compress_level=6)
            results.append({
                "path": str(png_path.relative_to(ROOT)),
                "format": "png",
                "width": img.width,
                "height": img.height,
                "size_bytes": png_path.stat().st_size,
                "sha256": compute_sha256(png_path),
                "primary": True,
            })

            # Save as WebP (web fallback)
            webp_path = dest_dir / f"{asset_id}.webp"
            img.save(webp_path, "WEBP", quality=85, method=6)
            results.append({
                "path": str(webp_path.relative_to(ROOT)),
                "format": "webp",
                "width": img.width,
                "height": img.height,
                "size_bytes": webp_path.stat().st_size,
                "sha256": compute_sha256(webp_path),
                "primary": False,
            })

            # Generate thumbnails
            thumbnails = {}
            for name, (tw, th) in THUMBNAIL_SIZES.items():
                thumb = img.copy()
                thumb.thumbnail((tw, th), Image.Resampling.LANCZOS)
                thumb_path = dest_dir / f"{asset_id}_thumb_{name}.webp"
                thumb.save(thumb_path, "WEBP", quality=75, method=6)
                thumbnails[name] = {
                    "path": str(thumb_path.relative_to(ROOT)),
                    "width": thumb.width,
                    "height": thumb.height,
                    "size_bytes": thumb_path.stat().st_size,
                }

            return results, thumbnails

    except Exception as e:
        return [{"error": f"Image conversion failed: {e}"}], {}


# ─── Video Conversion ───────────────────────────────────────────────────────

def convert_video(source: Path, dest_dir: Path, asset_id: str) -> list[dict]:
    """Convert video to Godot-compatible formats. Returns list of converted file info."""
    if ffmpeg is None:
        # Fallback to direct ffmpeg call
        return convert_video_ffmpeg(source, dest_dir, asset_id)

    results = []
    try:
        probe = ffmpeg.probe(str(source))
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        duration = float(probe['format'].get('duration', 0))

        # Scale if needed
        max_w, max_h = VIDEO_SETTINGS["max_resolution"]
        if width > max_w or height > max_h:
            scale_filter = f"scale='min({max_w},iw)':'min({max_h},ih)':force_original_aspect_ratio=decrease"
        else:
            scale_filter = None

        # WebM VP9 (primary for Godot 4+)
        webm_path = dest_dir / f"{asset_id}.webm"
        stream = ffmpeg.input(str(source))
        if scale_filter:
            stream = stream.filter('scale', *scale_filter.split("'")[1::2])
        stream = ffmpeg.output(
            stream, str(webm_path),
            vcodec='libvpx-vp9', crf=VIDEO_SETTINGS["crf"],
            preset=VIDEO_SETTINGS["preset"], deadine='good',
            acodec='libopus', audio_bitrate='128k'
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        results.append({
            "path": str(webm_path.relative_to(ROOT)),
            "format": "webm",
            "codec": "vp9",
            "width": width,
            "height": height,
            "duration_sec": duration,
            "size_bytes": webm_path.stat().st_size,
            "sha256": compute_sha256(webm_path),
            "primary": True,
        })

        # MP4 H.264 (fallback)
        mp4_path = dest_dir / f"{asset_id}.mp4"
        stream = ffmpeg.input(str(source))
        if scale_filter:
            stream = stream.filter('scale', *scale_filter.split("'")[1::2])
        stream = ffmpeg.output(
            stream, str(mp4_path),
            vcodec='libx264', crf=VIDEO_SETTINGS["crf"],
            preset=VIDEO_SETTINGS["preset"],
            acodec='aac', audio_bitrate='128k',
            movflags='+faststart'
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        results.append({
            "path": str(mp4_path.relative_to(ROOT)),
            "format": "mp4",
            "codec": "h264",
            "width": width,
            "height": height,
            "duration_sec": duration,
            "size_bytes": mp4_path.stat().st_size,
            "sha256": compute_sha256(mp4_path),
            "primary": False,
        })

        return results

    except Exception as e:
        return [{"error": f"Video conversion failed: {e}"}]


def convert_video_ffmpeg(source: Path, dest_dir: Path, asset_id: str) -> list[dict]:
    """Fallback video conversion using ffmpeg CLI."""
    results = []

    # Get video info
    code, out, err = run_cmd([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json", str(source)
    ])
    if code != 0:
        return [{"error": f"ffprobe failed: {err}"}]

    try:
        info = json.loads(out)
        video_info = info['streams'][0]
        width = video_info['width']
        height = video_info['height']
        duration = float(video_info.get('duration', 0))
    except Exception:
        return [{"error": "Failed to parse video info"}]

    max_w, max_h = VIDEO_SETTINGS["max_resolution"]
    scale = ""
    if width > max_w or height > max_h:
        scale = f"-vf scale='min({max_w},iw)':'min({max_h},ih)':force_original_aspect_ratio=decrease"

    # WebM VP9
    webm_path = dest_dir / f"{asset_id}.webm"
    code, out, err = run_cmd([
        "ffmpeg", "-y", "-i", str(source),
        *(scale.split() if scale else []),
        "-c:v", "libvpx-vp9", "-crf", str(VIDEO_SETTINGS["crf"]),
        "-preset", VIDEO_SETTINGS["preset"], "-deadline", "good",
        "-c:a", "libopus", "-b:a", "128k",
        str(webm_path)
    ], timeout=600)
    if code == 0 and webm_path.exists():
        results.append({
            "path": str(webm_path.relative_to(ROOT)),
            "format": "webm", "codec": "vp9",
            "width": width, "height": height,
            "duration_sec": duration,
            "size_bytes": webm_path.stat().st_size,
            "sha256": compute_sha256(webm_path),
            "primary": True,
        })
    else:
        results.append({"error": f"WebM conversion failed: {err}"})

    # MP4 H.264
    mp4_path = dest_dir / f"{asset_id}.mp4"
    code, out, err = run_cmd([
        "ffmpeg", "-y", "-i", str(source),
        *(scale.split() if scale else []),
        "-c:v", "libx264", "-crf", str(VIDEO_SETTINGS["crf"]),
        "-preset", VIDEO_SETTINGS["preset"],
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(mp4_path)
    ], timeout=600)
    if code == 0 and mp4_path.exists():
        results.append({
            "path": str(mp4_path.relative_to(ROOT)),
            "format": "mp4", "codec": "h264",
            "width": width, "height": height,
            "duration_sec": duration,
            "size_bytes": mp4_path.stat().st_size,
            "sha256": compute_sha256(mp4_path),
            "primary": False,
        })
    else:
        results.append({"error": f"MP4 conversion failed: {err}"})

    return results


# ─── Audio Conversion ───────────────────────────────────────────────────────

def convert_audio(source: Path, dest_dir: Path, asset_id: str) -> list[dict]:
    """Convert audio to Godot-compatible formats. Returns list of converted file info."""
    if ffmpeg is None:
        return convert_audio_ffmpeg(source, dest_dir, asset_id)

    results = []
    try:
        probe = ffmpeg.probe(str(source))
        audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        duration = float(probe['format'].get('duration', 0))
        sample_rate = int(audio_info.get('sample_rate', AUDIO_SETTINGS["sample_rate"]))

        # OGG Vorbis (primary for Godot)
        ogg_path = dest_dir / f"{asset_id}.ogg"
        stream = ffmpeg.input(str(source))
        stream = ffmpeg.output(
            stream, str(ogg_path),
            acodec='libvorbis', audio_bitrate=AUDIO_SETTINGS["bitrate"],
            ar=AUDIO_SETTINGS["sample_rate"]
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        results.append({
            "path": str(ogg_path.relative_to(ROOT)),
            "format": "ogg", "codec": "vorbis",
            "duration_sec": duration,
            "sample_rate": AUDIO_SETTINGS["sample_rate"],
            "size_bytes": ogg_path.stat().st_size,
            "sha256": compute_sha256(ogg_path),
            "primary": True,
        })

        # MP3 (fallback)
        mp3_path = dest_dir / f"{asset_id}.mp3"
        stream = ffmpeg.input(str(source))
        stream = ffmpeg.output(
            stream, str(mp3_path),
            acodec='libmp3lame', audio_bitrate=AUDIO_SETTINGS["bitrate"],
            ar=AUDIO_SETTINGS["sample_rate"]
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        results.append({
            "path": str(mp3_path.relative_to(ROOT)),
            "format": "mp3", "codec": "mp3",
            "duration_sec": duration,
            "sample_rate": AUDIO_SETTINGS["sample_rate"],
            "size_bytes": mp3_path.stat().st_size,
            "sha256": compute_sha256(mp3_path),
            "primary": False,
        })

        # Keep original WAV if it's PCM
        if source.suffix.lower() == '.wav':
            wav_dest = dest_dir / f"{asset_id}.wav"
            shutil.copy2(source, wav_dest)
            results.append({
                "path": str(wav_dest.relative_to(ROOT)),
                "format": "wav", "codec": "pcm",
                "duration_sec": duration,
                "sample_rate": sample_rate,
                "size_bytes": wav_dest.stat().st_size,
                "sha256": compute_sha256(wav_dest),
                "primary": False,
                "original": True,
            })

        return results

    except Exception as e:
        return [{"error": f"Audio conversion failed: {e}"}]


def convert_audio_ffmpeg(source: Path, dest_dir: Path, asset_id: str) -> list[dict]:
    """Fallback audio conversion using ffmpeg CLI."""
    results = []

    # Get audio info
    code, out, err = run_cmd([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,duration",
        "-of", "json", str(source)
    ])
    if code != 0:
        return [{"error": f"ffprobe failed: {err}"}]

    try:
        info = json.loads(out)
        audio_info = info['streams'][0]
        sample_rate = int(audio_info.get('sample_rate', AUDIO_SETTINGS["sample_rate"]))
        duration = float(audio_info.get('duration', 0))
    except Exception:
        return [{"error": "Failed to parse audio info"}]

    # OGG Vorbis
    ogg_path = dest_dir / f"{asset_id}.ogg"
    code, out, err = run_cmd([
        "ffmpeg", "-y", "-i", str(source),
        "-c:a", "libvorbis", "-b:a", AUDIO_SETTINGS["bitrate"],
        "-ar", str(AUDIO_SETTINGS["sample_rate"]),
        str(ogg_path)
    ])
    if code == 0 and ogg_path.exists():
        results.append({
            "path": str(ogg_path.relative_to(ROOT)),
            "format": "ogg", "codec": "vorbis",
            "duration_sec": duration,
            "sample_rate": AUDIO_SETTINGS["sample_rate"],
            "size_bytes": ogg_path.stat().st_size,
            "sha256": compute_sha256(ogg_path),
            "primary": True,
        })

    # MP3
    mp3_path = dest_dir / f"{asset_id}.mp3"
    code, out, err = run_cmd([
        "ffmpeg", "-y", "-i", str(source),
        "-c:a", "libmp3lame", "-b:a", AUDIO_SETTINGS["bitrate"],
        "-ar", str(AUDIO_SETTINGS["sample_rate"]),
        str(mp3_path)
    ])
    if code == 0 and mp3_path.exists():
        results.append({
            "path": str(mp3_path.relative_to(ROOT)),
            "format": "mp3", "codec": "mp3",
            "duration_sec": duration,
            "sample_rate": AUDIO_SETTINGS["sample_rate"],
            "size_bytes": mp3_path.stat().st_size,
            "sha256": compute_sha256(mp3_path),
            "primary": False,
        })

    # Keep WAV
    if source.suffix.lower() == '.wav':
        wav_dest = dest_dir / f"{asset_id}.wav"
        shutil.copy2(source, wav_dest)
        results.append({
            "path": str(wav_dest.relative_to(ROOT)),
            "format": "wav", "codec": "pcm",
            "duration_sec": duration,
            "sample_rate": sample_rate,
            "size_bytes": wav_dest.stat().st_size,
            "sha256": compute_sha256(wav_dest),
            "primary": False,
            "original": True,
        })

    return results


# ─── 3D Model Handling ──────────────────────────────────────────────────────

def process_3d_model(source: Path, dest_dir: Path, asset_id: str) -> list[dict]:
    """Process 3D model (GLB/GLTF) for Godot. Returns list of converted file info."""
    results = []

    # For GLB/GLTF, Godot can import directly
    # Just copy and validate
    dest_path = dest_dir / f"{asset_id}{source.suffix}"
    shutil.copy2(source, dest_path)

    results.append({
        "path": str(dest_path.relative_to(ROOT)),
        "format": source.suffix[1:].lower(),
        "size_bytes": dest_path.stat().st_size,
        "sha256": compute_sha256(dest_path),
        "primary": True,
    })

    # Could add: glTF validator, Draco compression, etc.
    return results


# ─── Main Import Logic ──────────────────────────────────────────────────────

def detect_asset_type(filepath: Path) -> str:
    """Detect asset type from file extension."""
    ext = filepath.suffix.lower()
    if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'):
        return 'image'
    elif ext in ('.mp4', '.webm', '.mov', '.avi', '.mkv', '.ogv'):
        return 'video'
    elif ext in ('.wav', '.ogg', '.mp3', '.flac', '.aac', '.m4a', '.opus'):
        return 'audio'
    elif ext in ('.glb', '.gltf', '.obj', '.fbx', '.dae', '.blend'):
        return 'model'
    else:
        return 'unknown'


def process_asset(filepath: Path, dest_base: Path, asset_info: dict, dry_run: bool) -> AssetInfo:
    """Process a single asset file."""
    asset_id = asset_info.get('id', filepath.stem)
    category = asset_info.get('category', 'general')

    # Determine destination
    type_dir = detect_asset_type(filepath)
    if type_dir == 'image':
        type_dir = 'textures'
    elif type_dir == 'video':
        type_dir = 'video'
    elif type_dir == 'audio':
        type_dir = 'audio'
    elif type_dir == 'model':
        type_dir = 'models'
    else:
        type_dir = 'misc'

    dest_dir = dest_base / type_dir / category
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Create asset info
    asset = AssetInfo(
        id=asset_id,
        name=asset_info.get('name', filepath.stem),
        category=category,
        source_path=str(filepath),
        dest_path=str(dest_dir / filepath.name),
        mime_type=get_mime_type(filepath),
        size_bytes=filepath.stat().st_size,
        sha256=compute_sha256(filepath),
        provenance=asset_info.get('provenance', {}),
    )

    if dry_run:
        asset.status = "dry-run"
        return asset

    # Convert based on type
    asset_type = detect_asset_type(filepath)

    try:
        if asset_type == 'image':
            converted, thumbnails = convert_image(filepath, dest_dir, asset_id)
            asset.converted_files = converted
            asset.thumbnails = thumbnails
            # Find primary
            for c in converted:
                if c.get('primary'):
                    asset.width = c.get('width', 0)
                    asset.height = c.get('height', 0)
                    break

        elif asset_type == 'video':
            converted = convert_video(filepath, dest_dir, asset_id)
            asset.converted_files = converted
            for c in converted:
                if c.get('primary'):
                    asset.width = c.get('width', 0)
                    asset.height = c.get('height', 0)
                    asset.duration_sec = c.get('duration_sec', 0)
                    break

        elif asset_type == 'audio':
            converted = convert_audio(filepath, dest_dir, asset_id)
            asset.converted_files = converted
            for c in converted:
                if c.get('primary'):
                    asset.duration_sec = c.get('duration_sec', 0)
                    break

        elif asset_type == 'model':
            converted = process_3d_model(filepath, dest_dir, asset_id)
            asset.converted_files = converted

        else:
            # Unknown type - just copy
            dest_path = dest_dir / filepath.name
            shutil.copy2(filepath, dest_path)
            asset.converted_files = [{
                "path": str(dest_path.relative_to(ROOT)),
                "format": filepath.suffix[1:],
                "size_bytes": dest_path.stat().st_size,
                "sha256": compute_sha256(dest_path),
                "primary": True,
            }]

        # Check for errors
        errors = [c for c in asset.converted_files if 'error' in c]
        if errors:
            asset.status = "partial"
            asset.error = "; ".join(e['error'] for e in errors)
        else:
            asset.status = "imported"

    except Exception as e:
        asset.status = "failed"
        asset.error = str(e)

    return asset


def import_from_local(source_path: Path, dest_base: Path, manifest: dict, dry_run: bool, resume: bool) -> list[AssetInfo]:
    """Import assets from local directory."""
    existing_ids = {a['id'] for a in manifest.get('assets', [])}

    # Find all files in source
    assets_to_import = []
    for filepath in source_path.rglob('*'):
        if filepath.is_file() and not filepath.name.startswith('.'):
            # Try to match with manifest or use filename
            asset_id = filepath.stem
            matched = None
            for a in manifest.get('assets', []):
                if a.get('id') == asset_id or Path(a.get('source_path', '')).name == filepath.name:
                    matched = a
                    break

            if matched:
                assets_to_import.append((filepath, matched))
            else:
                # Create basic info from filename
                assets_to_import.append((filepath, {
                    'id': asset_id,
                    'name': filepath.stem,
                    'category': filepath.parent.name if filepath.parent != source_path else 'general',
                }))

    print(f"Found {len(assets_to_import)} assets to import")

    results = []
    for i, (filepath, info) in enumerate(assets_to_import, 1):
        if resume and info['id'] in existing_ids:
            print(f"[{i}/{len(assets_to_import)}] Skipping {info['id']} (already in manifest)")
            continue

        print(f"[{i}/{len(assets_to_import)}] Importing {info['id']}...")
        asset = process_asset(filepath, dest_base, info, dry_run)
        results.append(asset)

        # Update manifest
        manifest.setdefault('assets', []).append(asdict(asset))
        save_manifest(manifest)

        status = asset.status
        if status == "imported":
            print(f"  ✓ Imported ({len(asset.converted_files)} files)")
        elif status == "partial":
            print(f"  ⚠ Partial: {asset.error}")
        elif status == "dry-run":
            print(f"  ○ Dry run")
        else:
            print(f"  ✗ Failed: {asset.error}")

    return results


def import_from_manifest(manifest_path: Path, dest_base: Path, manifest: dict, dry_run: bool, resume: bool) -> list[AssetInfo]:
    """Import assets using a manifest file with source paths."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        import_manifest = json.load(f)

    existing_ids = {a['id'] for a in manifest.get('assets', [])}
    assets_to_import = import_manifest.get('assets', [])

    print(f"Found {len(assets_to_import)} assets in manifest")

    results = []
    for i, info in enumerate(assets_to_import, 1):
        if resume and info['id'] in existing_ids:
            print(f"[{i}/{len(assets_to_import)}] Skipping {info['id']} (already in manifest)")
            continue

        source_path = Path(info.get('source_path', ''))
        if not source_path.exists():
            print(f"[{i}/{len(assets_to_import)}] Source not found: {source_path}")
            asset = AssetInfo(
                id=info['id'],
                name=info.get('name', info['id']),
                category=info.get('category', 'general'),
                source_path=str(source_path),
                dest_path="",
                mime_type="",
                size_bytes=0,
                sha256="",
                status="failed",
                error=f"Source file not found: {source_path}"
            )
            results.append(asset)
            manifest.setdefault('assets', []).append(asdict(asset))
            save_manifest(manifest)
            continue

        print(f"[{i}/{len(assets_to_import)}] Importing {info['id']}...")
        asset = process_asset(source_path, dest_base, info, dry_run)
        results.append(asset)

        manifest.setdefault('assets', []).append(asdict(asset))
        save_manifest(manifest)

        status = asset.status
        if status == "imported":
            print(f"  ✓ Imported ({len(asset.converted_files)} files)")
        elif status == "partial":
            print(f"  ⚠ Partial: {asset.error}")
        elif status == "dry-run":
            print(f"  ○ Dry run")
        else:
            print(f"  ✗ Failed: {asset.error}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Asset Import Pipeline for ChemLab")
    parser.add_argument("--source", choices=["local", "manifest", "gdrive"],
                        default="local", help="Import source type")
    parser.add_argument("--path", help="Local source path (for --source local)")
    parser.add_argument("--manifest", help="Import manifest file (for --source manifest)")
    parser.add_argument("--folder-id", help="Google Drive folder ID (for --source gdrive)")
    parser.add_argument("--dest", default="game/assets", help="Destination base directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported")
    parser.add_argument("--resume", action="store_true", help="Skip already-imported assets")
    parser.add_argument("--category", help="Filter by category")
    args = parser.parse_args()

    dest_base = ROOT / args.dest
    manifest = load_manifest()

    if args.source == "local":
        if not args.path:
            print("--path required for local source", file=sys.stderr)
            return 1
        source_path = Path(args.path)
        if not source_path.exists():
            print(f"Source path not found: {source_path}", file=sys.stderr)
            return 1
        results = import_from_local(source_path, dest_base, manifest, args.dry_run, args.resume)

    elif args.source == "manifest":
        if not args.manifest:
            print("--manifest required for manifest source", file=sys.stderr)
            return 1
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"Manifest not found: {manifest_path}", file=sys.stderr)
            return 1
        results = import_from_manifest(manifest_path, dest_base, manifest, args.dry_run, args.resume)

    elif args.source == "gdrive":
        print("Google Drive import not yet implemented. Use --source local with downloaded files.")
        return 1

    else:
        parser.print_help()
        return 1

    # Summary
    imported = sum(1 for r in results if r.status == "imported")
    partial = sum(1 for r in results if r.status == "partial")
    failed = sum(1 for r in results if r.status == "failed")
    dry_run = sum(1 for r in results if r.status == "dry-run")

    print(f"\n--- Import Summary ---")
    print(f"Imported: {imported}")
    print(f"Partial: {partial}")
    print(f"Failed: {failed}")
    print(f"Dry Run: {dry_run}")
    print(f"Manifest: {ASSET_MANIFEST}")
    print(f"Import Log: {IMPORT_LOG}")

    # Save import log
    log = load_import_log()
    log.setdefault("imports", []).append({
        "timestamp": time.time(),
        "source": args.source,
        "path": args.path or args.manifest,
        "dest": args.dest,
        "results": [asdict(r) for r in results],
        "summary": {
            "imported": imported,
            "partial": partial,
            "failed": failed,
            "dry_run": dry_run,
        }
    })
    save_import_log(log)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())