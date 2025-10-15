import os
import re
import argparse
from typing import Dict, List, Tuple
from video_editor import build_video


def _safe_title(title: str) -> str:
    return re.sub(r"[\\/*?:\"<>|]", "_", title).strip()


def _find_images(title: str, images_dir: str = "data/images") -> List[str]:
    safe = _safe_title(title)
    comic_dir = os.path.join(images_dir, safe)
    if not os.path.isdir(comic_dir):
        raise FileNotFoundError(f"Images folder not found: {comic_dir}")

    files = [f for f in os.listdir(comic_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    # sort by scene_#.ext
    def _scene_index(name: str) -> int:
        m = re.search(r"scene_(\d+)", name, re.IGNORECASE)
        return int(m.group(1)) if m else 10**9

    files.sort(key=_scene_index)
    return [os.path.join(comic_dir, f) for f in files]


def _find_audio_map(title: str, narration_dir: str = "data/narration") -> Dict[str, str]:
    safe = _safe_title(title)
    story_dir = os.path.join(narration_dir, safe, "audio")
    if not os.path.isdir(story_dir):
        raise FileNotFoundError(f"Audio folder not found: {story_dir}")

    audio_map: Dict[str, str] = {}
    for f in os.listdir(story_dir):
        if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac")):
            m = re.search(r"scene_(\d+)", f, re.IGNORECASE)
            if m:
                idx = int(m.group(1))
                audio_map[f"scene_{idx}"] = os.path.join(story_dir, f)
    if not audio_map:
        raise FileNotFoundError(f"No scene audio files found in {story_dir}")
    return audio_map


def _parse_resolution(res_text: str) -> Tuple[int, int]:
    if "x" in res_text:
        w, h = res_text.lower().split("x", 1)
        return int(w), int(h)
    if res_text == "1080p":
        return 1920, 1080
    if res_text == "720p":
        return 1280, 720
    raise ValueError("Unsupported resolution format. Use WxH (e.g., 1920x1080) or 1080p/720p.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build video from existing images and narration audio")
    parser.add_argument("--title", required=True, help="Topic title used for folders (e.g., 'Charlie Chaplin')")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--resolution", default="1920x1080", help="WxH or 1080p/720p")
    parser.add_argument("--crossfade", type=float, default=0.3)
    parser.add_argument("--min_scene_seconds", type=float, default=2.0)
    parser.add_argument("--head_pad", type=float, default=0.15)
    parser.add_argument("--tail_pad", type=float, default=0.15)
    parser.add_argument("--bgm", default="", help="Optional background music file path")
    parser.add_argument("--bgm_volume", type=float, default=0.08)
    parser.add_argument("--images_dir", default="data/images")
    parser.add_argument("--narration_dir", default="data/narration")
    parser.add_argument("--out_dir", default="data/videos")
    args = parser.parse_args()

    title = args.title
    images = _find_images(title, images_dir=args.images_dir)
    if not images:
        raise FileNotFoundError("No images found for the given title.")

    audio_map = _find_audio_map(title, narration_dir=args.narration_dir)

    w, h = _parse_resolution(args.resolution)
    out_dir = os.path.join(args.out_dir, _safe_title(title))
    os.makedirs(out_dir, exist_ok=True)

    result = build_video(
        images=images,
        scene_audio=audio_map,
        out_dir=out_dir,
        title=title,
        fps=int(args.fps),
        resolution=(w, h),
        crossfade_sec=float(args.crossfade),
        min_scene_seconds=float(args.min_scene_seconds),
        head_pad=float(args.head_pad),
        tail_pad=float(args.tail_pad),
        bg_music_path=args.bgm if args.bgm else None,
        bg_music_volume=float(args.bgm_volume)
    )

    print("Video created:", result["video_path"])


if __name__ == "__main__":
    main()

