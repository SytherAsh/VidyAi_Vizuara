import os
from typing import List, Dict, Any, Optional, Tuple


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def _estimate_scene_duration(audio_path: Optional[str], min_seconds: float, head_pad: float, tail_pad: float) -> float:
    duration = min_seconds
    if audio_path and os.path.exists(audio_path):
        try:
            from moviepy import editor as mpe  # local import to avoid module import errors at load time
            audio = mpe.AudioFileClip(audio_path)
            duration = max(min_seconds, audio.duration + head_pad + tail_pad)
            audio.close()
        except Exception:
            duration = max(min_seconds, head_pad + tail_pad)
    return duration


def build_video(
    images: List[str],
    scene_audio: Dict[str, str],
    out_dir: str,
    title: str,
    fps: int = 30,
    resolution: Tuple[int, int] = (1920, 1080),
    crossfade_sec: float = 0.3,
    min_scene_seconds: float = 2.0,
    head_pad: float = 0.15,
    tail_pad: float = 0.15,
    bg_music_path: Optional[str] = None,
    bg_music_volume: float = 0.08
) -> Dict[str, Any]:
    """
    Assemble a video from ordered images and per-scene narration audio files.

    Returns a dict containing output paths and per-scene timings.
    """
    try:
        from moviepy import editor as mpe
    except ImportError as e:
        raise ImportError("moviepy is required. Install with: pip install moviepy imageio-ffmpeg") from e
    _ensure_dir(out_dir)
    safe_title = title.replace('/', '_')
    video_path = os.path.join(out_dir, f"{safe_title}.mp4")

    # Prepare clips
    clips = []
    audio_tracks = []
    timings = []
    current_start = 0.0

    for idx, img_path in enumerate(images):
        scene_num = idx + 1
        scene_key = f"scene_{scene_num}"
        audio_path = scene_audio.get(scene_key)

        duration = _estimate_scene_duration(audio_path, min_scene_seconds, head_pad, tail_pad)

        img_clip = mpe.ImageClip(img_path).resize(newsize=resolution).set_duration(duration)
        if crossfade_sec > 0 and clips:
            img_clip = img_clip.crossfadein(crossfade_sec)
        clips.append(img_clip)

        if audio_path and os.path.exists(audio_path):
            narr = mpe.AudioFileClip(audio_path)
            narr = narr.fadein(head_pad)
            narr = narr.fadeout(tail_pad)
            audio_tracks.append(narr.set_start(current_start))

        timings.append({
            "scene": scene_num,
            "start": current_start,
            "end": current_start + duration,
            "duration": duration,
            "image": img_path,
            "audio": audio_path if audio_path and os.path.exists(audio_path) else None
        })

        current_start += duration - (crossfade_sec if crossfade_sec > 0 else 0)

    # Concatenate video
    final_video = mpe.concatenate_videoclips(clips, method="compose")

    # Compose audio (narration + optional music)
    if audio_tracks:
        base_audio = mpe.CompositeAudioClip(audio_tracks)
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                music = mpe.AudioFileClip(bg_music_path)
                music = music.volumex(bg_music_volume)
                music = music.set_start(0).set_duration(final_video.duration)
                final_video = final_video.set_audio(mpe.CompositeAudioClip([music, base_audio]))
            except Exception:
                final_video = final_video.set_audio(base_audio)
        else:
            final_video = final_video.set_audio(base_audio)

    final_video.write_videofile(
        video_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        temp_audiofile=os.path.join(out_dir, "temp-audio.m4a"),
        remove_temp=True
    )

    # Close resources
    try:
        for clip in clips:
            clip.close()
        if 'base_audio' in locals():
            base_audio.close()
        if 'music' in locals():
            music.close()
        final_video.close()
    except Exception:
        pass

    return {"video_path": video_path, "timings": timings}


