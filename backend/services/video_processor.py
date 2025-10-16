import os
import json
import subprocess
import uuid
from typing import List, Dict, Optional
import os


def _search_local_storage_for_file(candidate_keys: List[str]) -> Optional[str]:
    """Best-effort search for a local file matching any candidate key's basename."""
    filenames = {os.path.basename(k) for k in candidate_keys if isinstance(k, str)}
    for root, _, files in os.walk("local_storage"):
        for name in files:
            if name in filenames:
                candidate = os.path.join(root, name)
                if os.path.exists(candidate):
                    return candidate
    return None


def _fallback_latest_user_file(user_id: int) -> Optional[str]:
    user_paid = os.path.join("local_storage", "uploads", "paid", str(user_id))
    user_free = os.path.join("local_storage", "uploads", "free", str(user_id))
    for user_dir in (user_paid, user_free):
        if os.path.isdir(user_dir):
            candidates = [
                os.path.join(user_dir, f)
                for f in os.listdir(user_dir)
                if os.path.isfile(os.path.join(user_dir, f)) and f.lower().endswith(".mp4")
            ]
            if candidates:
                candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return candidates[0]
    return None


def resolve_input_path(original_file_path: Optional[str], processed_file_path: Optional[str], user_id: int) -> str:
    """Resolve an actual input file path for ffmpeg from stored DB paths."""
    candidate_keys = [k for k in [original_file_path, processed_file_path] if k]

    # Absolute path first
    for key in candidate_keys:
        if os.path.isabs(key) and os.path.exists(key):
            return key

    # Search local_storage
    found = _search_local_storage_for_file(candidate_keys)
    if found:
        return found

    # Fallback: pick most recent user file when key basenames don't match
    latest = _fallback_latest_user_file(user_id)
    if latest:
        return latest

    raise FileNotFoundError("Input video file not found in local storage")


def build_delogo_filter(watermarks: List[Dict]) -> Optional[str]:
    """Build an improved ffmpeg filter chain for better watermark removal.

    Uses enhanced delogo parameters and post-processing for better quality."""
    steps = []
    for wm in watermarks:
        try:
            x = int(round(float(wm.get("x", 0))))
            y = int(round(float(wm.get("y", 0))))
            w = int(round(float(wm.get("width", 0))))
            h = int(round(float(wm.get("height", 0))))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue
        # Basic delogo filter for maximum compatibility
        steps.append(f"delogo=x={x}:y={y}:w={w}:h={h}:show=0")
    
    if not steps:
        return None
    
    # Add post-processing for better quality
    filter_chain = ",".join(steps)
    
    # Add unsharp mask for sharpness and temporal smoothing
    filter_chain += ",unsharp=5:5:0.8:3:3:0.4"
    
    return filter_chain


def process_video_with_delogo(
    original_file_path: Optional[str],
    processed_file_path: Optional[str],
    watermark_selections_json: Optional[str],
    user_id: int,
) -> str:
    """Run ffmpeg to remove watermarks and return the output path.

    Creates backend/local_storage/processed/{user_id}/{uuid}.mp4
    """
    input_path = resolve_input_path(original_file_path, processed_file_path, user_id)

    selections: List[Dict] = []
    if watermark_selections_json:
        try:
            data = json.loads(watermark_selections_json)
            if isinstance(data, dict) and "watermarks" in data:
                selections = data["watermarks"] or []
            elif isinstance(data, list):
                selections = data
        except Exception:
            selections = []

    filter_chain = build_delogo_filter(selections)
    # Debug logging of selections and filter used
    try:
        print(f"🎯 Watermark selections parsed: {len(selections)} items")
        if selections:
            print(f"🔧 delogo filter: {filter_chain}")
    except Exception:
        pass

    # Prepare output path
    out_dir = os.path.join("local_storage", "processed", str(user_id))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{uuid.uuid4()}.mp4")

    # Build ffmpeg command (allow override via env)
    ffmpeg_bin = os.getenv("FFMPEG_BIN", "ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        input_path,
    ]

    if filter_chain:
        cmd += ["-vf", filter_chain]

    # Re-encode video with higher quality settings for better results
    cmd += [
        "-c:v", "libx264",
        "-preset", "medium",  # Better quality than veryfast
        "-crf", "18",         # Higher quality than 23
        "-c:a", "aac",
        "-movflags", "+faststart",
        out_path,
    ]

    try:
        print(f"▶️ Running FFmpeg: {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        # Log tail of stderr which includes filter details
        if proc.stderr:
            tail = proc.stderr.splitlines()[-20:]
            print("FFmpeg stderr tail:\n" + "\n".join(tail))
    except FileNotFoundError as e:
        raise RuntimeError(
            "FFmpeg not found. Install FFmpeg and ensure it's on PATH, or set FFMPEG_BIN to the full path of ffmpeg.exe"
        ) from e
    except subprocess.CalledProcessError as e:
        # Surface ffmpeg error
        raise RuntimeError(f"FFmpeg failed: {e.stderr[-1000:]}" if e.stderr else "FFmpeg failed") from e

    if not os.path.exists(out_path):
        raise RuntimeError("Processed file was not created")

    return out_path


