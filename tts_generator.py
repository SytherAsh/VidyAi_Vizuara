import os
import asyncio
from typing import Dict, Any, List, Optional
import edge_tts


def ensure_directory(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


async def _synthesize_to_mp3_async(text: str, output_path: str, voice: str = "en-IN-NeerjaNeural", rate: str = "+0%", volume: str = "+0%") -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(output_path)


def synthesize_to_mp3(text: str, output_path: str, voice: str = "en-IN-NeerjaNeural", rate: str = "+0%", volume: str = "+0%") -> None:
    """
    Synthesize the given text to an MP3 file using Microsoft Edge TTS voices.
    This is a sync wrapper suitable for Streamlit callbacks.
    """
    ensure_directory(os.path.dirname(output_path))
    try:
        asyncio.run(_synthesize_to_mp3_async(text, output_path, voice=voice, rate=rate, volume=volume))
    except RuntimeError:
        # If there's already an event loop (e.g., in certain environments), use it differently
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task and wait for it
            task = loop.create_task(_synthesize_to_mp3_async(text, output_path, voice=voice, rate=rate, volume=volume))
            loop.run_until_complete(task)
        else:
            loop.run_until_complete(_synthesize_to_mp3_async(text, output_path, voice=voice, rate=rate, volume=volume))


def estimate_tts_duration_seconds(text: str) -> float:
    """
    Rough estimate for English: ~2.5 words/sec.
    """
    words = [w for w in text.strip().split() if w]
    return max(0.0, len(words) / 2.5)


def generate_scene_audios(narrations: Dict[str, Any], title: str, base_dir: str = "data/narration", voice: str = "en-IN-NeerjaNeural", rate: str = "+0%", volume: str = "+0%") -> Dict[str, str]:
    """
    Generate MP3 files per scene from a narrations dict produced by NarrationGenerator.

    Returns a mapping of scene keys to generated MP3 paths, plus a 'merged' key placeholder.
    """
    safe_title = title.replace('/', '_')
    out_dir = os.path.join(base_dir, safe_title, "audio")
    ensure_directory(out_dir)

    scene_to_path: Dict[str, str] = {}
    narrs = narrations.get("narrations", {})
    for scene_key, scene_data in narrs.items():
        scene_num = scene_data.get("scene_number")
        text = scene_data.get("narration", "").strip()
        if not text:
            continue
        mp3_path = os.path.join(out_dir, f"scene_{scene_num}.mp3")
        synthesize_to_mp3(text, mp3_path, voice=voice, rate=rate, volume=volume)
        scene_to_path[scene_key] = mp3_path

    return scene_to_path


