#!/usr/bin/env python3
"""
Comprehensive Video Creator from Existing Images and Audio
Combines functionality from build_video_from_existing.py, create_video.py, and test_video.py

Usage:
    python video_creator.py                           # Interactive mode
    python video_creator.py "Charlie Chaplin"         # Quick mode with topic
    python video_creator.py --title "Charlie Chaplin" # Command line mode with options
"""

import os
import sys
import re
import argparse
from typing import Dict, List, Tuple, Optional

# Import video_editor module
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from video_editor import build_video


def _safe_title(title: str) -> str:
    """Convert title to safe filename"""
    return re.sub(r"[\\/*?:\"<>|]", "_", title).strip()


def _find_images(title: str, images_dir: str = "data/images") -> List[str]:
    """Find all image files for a given title, sorted by scene number"""
    safe = _safe_title(title)
    comic_dir = os.path.join(images_dir, safe)
    if not os.path.isdir(comic_dir):
        raise FileNotFoundError(f"Images folder not found: {comic_dir}")

    files = [f for f in os.listdir(comic_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    # Sort by scene_#.ext
    def _scene_index(name: str) -> int:
        m = re.search(r"scene_(\d+)", name, re.IGNORECASE)
        return int(m.group(1)) if m else 10**9

    files.sort(key=_scene_index)
    return [os.path.join(comic_dir, f) for f in files]


def _find_audio_map(title: str, narration_dir: str = "data/narration") -> Dict[str, str]:
    """Find all audio files for a given title, mapped by scene number"""
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
    """Parse resolution string to width, height tuple"""
    if "x" in res_text:
        w, h = res_text.lower().split("x", 1)
        return int(w), int(h)
    if res_text == "1080p":
        return 1920, 1080
    if res_text == "720p":
        return 1280, 720
    raise ValueError("Unsupported resolution format. Use WxH (e.g., 1920x1080) or 1080p/720p.")


def list_available_topics(images_dir: str = "data/images") -> List[str]:
    """List all available topics that have images"""
    if not os.path.exists(images_dir):
        print(f"❌ Images directory not found: {images_dir}")
        return []
    
    topics = []
    for item in os.listdir(images_dir):
        item_path = os.path.join(images_dir, item)
        if os.path.isdir(item_path):
            # Check if directory has image files
            image_files = [f for f in os.listdir(item_path) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if image_files:
                topics.append(item)
    
    return sorted(topics)


def list_available_audio_topics(narration_dir: str = "data/narration") -> List[str]:
    """List all available topics that have audio"""
    if not os.path.exists(narration_dir):
        print(f"❌ Narration directory not found: {narration_dir}")
        return []
    
    topics = []
    for item in os.listdir(narration_dir):
        item_path = os.path.join(narration_dir, item)
        if os.path.isdir(item_path):
            audio_dir = os.path.join(item_path, "audio")
            if os.path.exists(audio_dir):
                audio_files = [f for f in os.listdir(audio_dir) 
                              if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac'))]
                if audio_files:
                    topics.append(item)
    
    return sorted(topics)


def create_video(
    title: str,
    resolution: str = "1920x1080",
    fps: int = 30,
    crossfade: float = 0.3,
    min_scene_seconds: float = 2.0,
    head_pad: float = 0.15,
    tail_pad: float = 0.15,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.08,
    images_dir: str = "data/images",
    narration_dir: str = "data/narration",
    out_dir: str = "data/videos",
    use_audio: bool = True,
    verbose: bool = True
) -> Optional[Dict]:
    """Create video from existing images and audio"""
    
    if verbose:
        print(f"🎬 Creating video for '{title}'...")
        print(f"   Resolution: {resolution}")
        print(f"   FPS: {fps}")
        print(f"   Audio: {'Yes' if use_audio else 'No'}")
        print(f"   Background Music: {'Yes' if bgm_path else 'No'}")
    
    try:
        # Find images
        images = _find_images(title, images_dir)
        if verbose:
            print(f"✅ Found {len(images)} images")
        
        # Find audio if requested
        audio_map = {}
        if use_audio:
            try:
                audio_map = _find_audio_map(title, narration_dir)
                if verbose:
                    print(f"✅ Found {len(audio_map)} audio files")
            except FileNotFoundError as e:
                if verbose:
                    print(f"⚠️  {e}")
                use_audio = False
        
        # Parse resolution
        w, h = _parse_resolution(resolution)
        
        # Create output directory
        output_dir = os.path.join(out_dir, _safe_title(title))
        os.makedirs(output_dir, exist_ok=True)
        
        # Build video
        result = build_video(
            images=images,
            scene_audio=audio_map if use_audio else {},
            out_dir=output_dir,
            title=title,
            fps=fps,
            resolution=(w, h),
            crossfade_sec=crossfade,
            min_scene_seconds=min_scene_seconds,
            head_pad=head_pad,
            tail_pad=tail_pad,
            bg_music_path=bgm_path,
            bg_music_volume=bgm_volume
        )
        
        if verbose:
            print(f"🎉 Video created successfully!")
            print(f"📁 Location: {result['video_path']}")
            print(f"⏱️  Duration: {result.get('duration', 'Unknown')} seconds")
        
        return result
        
    except Exception as e:
        if verbose:
            print(f"❌ Error creating video: {e}")
        return None


def interactive_mode():
    """Interactive video creation with user prompts"""
    print("🎬 Video Creator from Existing Images and Audio")
    print("=" * 50)
    
    # List available topics
    print("\n📁 Available topics with images:")
    image_topics = list_available_topics()
    if not image_topics:
        print("❌ No topics with images found!")
        return
    
    for i, topic in enumerate(image_topics, 1):
        print(f"  {i}. {topic}")
    
    # Get user selection
    while True:
        try:
            choice = input(f"\n🎯 Select a topic (1-{len(image_topics)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(image_topics):
                    selected_topic = image_topics[idx]
                    break
            print("❌ Invalid selection. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return
    
    print(f"\n✅ Selected topic: {selected_topic}")
    
    # Check for audio
    print("\n🔊 Checking for audio files...")
    audio_topics = list_available_audio_topics()
    
    if selected_topic in audio_topics:
        print(f"✅ Audio found for '{selected_topic}'")
        use_audio = True
    else:
        print(f"⚠️  No audio found for '{selected_topic}'")
        print("Available audio topics:")
        for topic in audio_topics:
            print(f"  - {topic}")
        
        use_audio = input("\n🤔 Continue without audio? (y/n): ").lower().strip() == 'y'
        if not use_audio:
            print("👋 Goodbye!")
            return
    
    # Video settings
    print("\n⚙️  Video Settings:")
    print("1. Resolution: 1920x1080 (1080p)")
    print("2. Resolution: 1280x720 (720p)")
    print("3. Custom resolution")
    
    while True:
        res_choice = input("Select resolution (1-3): ").strip()
        if res_choice == "1":
            resolution = "1920x1080"
            break
        elif res_choice == "2":
            resolution = "1280x720"
            break
        elif res_choice == "3":
            resolution = input("Enter custom resolution (e.g., 1920x1080): ").strip()
            try:
                _parse_resolution(resolution)
                break
            except ValueError as e:
                print(f"❌ {e}")
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")
    
    # FPS setting
    fps = input("Enter FPS (default 30): ").strip()
    fps = int(fps) if fps.isdigit() else 30
    
    # Background music
    bgm_path = input("Enter background music file path (optional, press Enter to skip): ").strip()
    bgm_path = bgm_path if bgm_path and os.path.exists(bgm_path) else None
    
    if bgm_path:
        bgm_volume = input("Background music volume (0.0-1.0, default 0.08): ").strip()
        bgm_volume = float(bgm_volume) if bgm_volume else 0.08
    else:
        bgm_volume = 0.08
    
    # Create video
    result = create_video(
        title=selected_topic,
        resolution=resolution,
        fps=fps,
        bgm_path=bgm_path,
        bgm_volume=bgm_volume,
        use_audio=use_audio
    )
    
    if result:
        print(f"\n✅ Video creation completed!")
    else:
        print(f"\n❌ Video creation failed!")


def quick_mode(topic: str, resolution: str = "1920x1080", fps: int = 30):
    """Quick video creation with minimal prompts"""
    print(f"🎬 Quick video creation for: {topic}")
    
    result = create_video(
        title=topic,
        resolution=resolution,
        fps=fps,
        use_audio=True
    )
    
    if result:
        print(f"✅ Quick video creation completed!")
        return result
    else:
        print(f"❌ Quick video creation failed!")
        return None


def main():
    """Main function with multiple usage modes"""
    parser = argparse.ArgumentParser(
        description="Create videos from existing images and narration audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python video_creator.py                                    # Interactive mode
  python video_creator.py "Charlie Chaplin"                 # Quick mode
  python video_creator.py --title "Charlie Chaplin"         # Command line mode
  python video_creator.py --title "Charlie Chaplin" --resolution 720p --fps 24
        """
    )
    
    parser.add_argument("--title", help="Topic title used for folders (e.g., 'Charlie Chaplin')")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--resolution", default="1920x1080", help="WxH or 1080p/720p")
    parser.add_argument("--crossfade", type=float, default=0.3, help="Crossfade duration in seconds")
    parser.add_argument("--min_scene_seconds", type=float, default=2.0, help="Minimum scene duration")
    parser.add_argument("--head_pad", type=float, default=0.15, help="Head padding in seconds")
    parser.add_argument("--tail_pad", type=float, default=0.15, help="Tail padding in seconds")
    parser.add_argument("--bgm", help="Background music file path")
    parser.add_argument("--bgm_volume", type=float, default=0.08, help="Background music volume (0.0-1.0)")
    parser.add_argument("--images_dir", default="data/images", help="Images directory")
    parser.add_argument("--narration_dir", default="data/narration", help="Narration directory")
    parser.add_argument("--out_dir", default="data/videos", help="Output directory")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (less output)")
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.title:
        # Command line mode with title specified
        result = create_video(
            title=args.title,
            resolution=args.resolution,
            fps=args.fps,
            crossfade=args.crossfade,
            min_scene_seconds=args.min_scene_seconds,
            head_pad=args.head_pad,
            tail_pad=args.tail_pad,
            bgm_path=args.bgm,
            bgm_volume=args.bgm_volume,
            images_dir=args.images_dir,
            narration_dir=args.narration_dir,
            out_dir=args.out_dir,
            use_audio=not args.no_audio,
            verbose=not args.quiet
        )
        
        if result and not args.quiet:
            print(f"Video created: {result['video_path']}")
        elif not result:
            sys.exit(1)
            
    elif len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        # Quick mode: python video_creator.py "topic"
        topic = sys.argv[1]
        result = quick_mode(topic)
        if not result:
            sys.exit(1)
            
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
