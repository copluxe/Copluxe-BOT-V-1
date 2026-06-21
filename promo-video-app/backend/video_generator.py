import os
import random
import numpy as np
from PIL import Image, ImageFilter
from typing import List, Optional, Dict
import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip

from text_generator import generate_text_overlays, detect_style
from music_matcher import select_music

TARGET_W = 1080
TARGET_H = 1920
FPS = 30


def preprocess_image(img_path: str) -> str:
    img = Image.open(img_path).convert("RGB")
    img_w, img_h = img.size

    # Scale to fill 1080x1920 (cover)
    scale = max(TARGET_W / img_w, TARGET_H / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - TARGET_W) // 2
    top = (new_h - TARGET_H) // 2
    img_cropped = img_resized.crop((left, top, left + TARGET_W, top + TARGET_H))

    # Save preprocessed
    out_path = img_path + "_prep.jpg"
    img_cropped.save(out_path, "JPEG", quality=95)
    return out_path


def create_kenburns_clip(img_path: str, duration: float) -> mp.VideoClip:
    prep_path = preprocess_image(img_path)
    clip = mp.ImageClip(prep_path).set_duration(duration)

    zoom_direction = random.choice(["in", "out"])
    # Slight pan direction
    pan_x = random.uniform(-0.05, 0.05)
    pan_y = random.uniform(-0.05, 0.05)

    def zoom_func(t):
        progress = t / duration
        if zoom_direction == "in":
            return 1.0 + 0.25 * progress
        else:
            return 1.25 - 0.25 * progress

    def position_func(t):
        progress = t / duration
        cx = 0.5 + pan_x * progress
        cy = 0.5 + pan_y * progress
        zoom = zoom_func(t)
        x = (cx - 0.5) * TARGET_W * (zoom - 1)
        y = (cy - 0.5) * TARGET_H * (zoom - 1)
        return ("center", "center")

    clip = clip.resize(zoom_func).set_position("center")
    return mp.CompositeVideoClip([clip], size=(TARGET_W, TARGET_H)).set_duration(duration)


def create_slide_clip(img_path: str, duration: float) -> mp.VideoClip:
    prep_path = preprocess_image(img_path)
    clip = mp.ImageClip(prep_path).set_duration(duration)
    direction = random.choice(["left", "right", "up", "down"])

    slide_duration = min(0.4, duration * 0.3)

    def position_func(t):
        if t >= slide_duration:
            return (0, 0)
        progress = t / slide_duration
        # Ease out
        progress = 1 - (1 - progress) ** 2

        if direction == "left":
            return (int(-TARGET_W + TARGET_W * progress), 0)
        elif direction == "right":
            return (int(TARGET_W - TARGET_W * progress), 0)
        elif direction == "up":
            return (0, int(-TARGET_H + TARGET_H * progress))
        else:
            return (0, int(TARGET_H - TARGET_H * progress))

    clip = clip.set_position(position_func)
    return mp.CompositeVideoClip([clip], size=(TARGET_W, TARGET_H)).set_duration(duration)


def create_cut_clip(img_path: str, duration: float) -> mp.VideoClip:
    prep_path = preprocess_image(img_path)
    clip = mp.ImageClip(prep_path).set_duration(duration)
    return mp.CompositeVideoClip([clip], size=(TARGET_W, TARGET_H)).set_duration(duration)


def create_image_clip(img_path: str, duration: float, transition: str) -> mp.VideoClip:
    if transition == "zoom":
        return create_kenburns_clip(img_path, duration)
    elif transition == "slide":
        return create_slide_clip(img_path, duration)
    else:
        return create_cut_clip(img_path, duration)


def make_text_clip(text: str, fontsize: int, color: str, duration: float,
                   stroke_color: str = "black", stroke_width: int = 3) -> mp.TextClip:
    try:
        clip = mp.TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font="DejaVu-Sans-Bold",
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(TARGET_W - 120, None),
            align="center",
        ).set_duration(duration)
    except Exception:
        # Fallback font
        clip = mp.TextClip(
            text,
            fontsize=fontsize,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(TARGET_W - 120, None),
            align="center",
        ).set_duration(duration)
    return clip


def add_text_overlays(base_clip: mp.VideoClip, overlays: List[Dict],
                      clip_durations: List[float], style_cfg: Dict) -> mp.VideoClip:
    text_clips = []
    current_time = 0.0
    color = style_cfg.get("font_color", "white")
    fontsize = style_cfg.get("font_size", 80)
    stroke_w = style_cfg.get("stroke_width", 3)
    position_pref = style_cfg.get("position", "center")

    for overlay in overlays:
        img_idx = overlay["image_index"]
        if img_idx >= len(clip_durations):
            continue

        clip_start = sum(clip_durations[:img_idx])
        clip_dur = clip_durations[img_idx]

        main_text = overlay["main_text"]
        cta_text = overlay["cta_text"]

        # Main text appears after 0.3s, lasts most of the clip
        main_dur = clip_dur - 0.4
        if main_dur <= 0:
            continue

        main_clip = make_text_clip(main_text, fontsize, color, main_dur, stroke_width=stroke_w)

        if position_pref == "top":
            main_y = 200
        elif position_pref == "bottom":
            main_y = TARGET_H - 400
        else:
            main_y = TARGET_H // 2 - 150

        main_clip = main_clip.set_position(("center", main_y)).set_start(clip_start + 0.3)
        text_clips.append(main_clip)

        # CTA text in last 1.5 seconds of clip
        cta_start = clip_start + max(clip_dur - 1.8, clip_start + 0.5)
        cta_dur = min(1.5, clip_dur - 0.3)
        if cta_dur > 0.2:
            cta_clip = make_text_clip(cta_text, fontsize - 25, color, cta_dur, stroke_width=stroke_w - 1)
            cta_clip = cta_clip.set_position(("center", main_y + 250)).set_start(cta_start)
            text_clips.append(cta_clip)

    if not text_clips:
        return base_clip

    return mp.CompositeVideoClip([base_clip] + text_clips, size=(TARGET_W, TARGET_H))


def generate_video(
    image_paths: List[str],
    description: str,
    output_path: str,
    variation_seed: Optional[int] = None,
) -> str:
    if variation_seed is not None:
        random.seed(variation_seed)
        np.random.seed(variation_seed)

    num_images = len(image_paths)
    # Duration: 10–60s, ~3–6s per image
    base_duration_per_clip = max(3.0, min(6.0, 60.0 / num_images))
    total_duration = base_duration_per_clip * num_images
    total_duration = max(10.0, min(60.0, total_duration))
    clip_duration = total_duration / num_images

    # Determine transitions
    transitions = []
    if num_images <= 4:
        # Fewer images: more zoom
        transition_pool = ["zoom", "zoom", "slide", "cut"]
    else:
        # More images: more variety
        transition_pool = ["zoom", "slide", "cut", "cut", "zoom"]

    for i in range(num_images):
        transitions.append(random.choice(transition_pool))

    # Build image clips
    clips = []
    clip_durations = []
    for i, img_path in enumerate(image_paths):
        dur = clip_duration
        # Vary duration slightly for natural feel
        if num_images > 4:
            dur = clip_duration * random.uniform(0.85, 1.15)
        clip_durations.append(dur)
        clips.append(create_image_clip(img_path, dur, transitions[i]))

    # Concatenate with cross-fades for zoom, hard cuts for cut
    final_clips = []
    for i, clip in enumerate(clips):
        if transitions[i] == "zoom" and i > 0:
            # Brief crossfade
            pass  # moviepy concatenate handles this
        final_clips.append(clip)

    video = mp.concatenate_videoclips(final_clips, method="compose")

    # Add text overlays
    style = detect_style(description)
    overlays = generate_text_overlays(description, num_images)
    if overlays:
        video = add_text_overlays(video, overlays, clip_durations,
                                  overlays[0]["style"] if overlays else {})

    # Add music
    actual_duration = video.duration
    music_path = select_music(description, style)
    if music_path and os.path.exists(music_path):
        try:
            audio = mp.AudioFileClip(music_path)
            if audio.duration < actual_duration:
                # Loop audio
                loops = int(actual_duration / audio.duration) + 1
                audio = mp.concatenate_audioclips([audio] * loops)
            audio = audio.subclip(0, actual_duration)
            # Fade out last 2 seconds
            audio = audio.audio_fadeout(2.0)
            video = video.set_audio(audio)
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        logger=None,
    )

    # Generate thumbnail (first frame of second clip)
    thumb_path = output_path.replace(".mp4", "_thumb.jpg")
    try:
        thumb_time = min(clip_durations[0] + 0.5, actual_duration * 0.3)
        frame = video.get_frame(thumb_time)
        thumb = Image.fromarray(frame)
        # Resize thumbnail to 540x960
        thumb = thumb.resize((540, 960), Image.LANCZOS)
        thumb.save(thumb_path, "JPEG", quality=85)
    except Exception:
        pass

    # Cleanup preprocessed images
    for img_path in image_paths:
        prep = img_path + "_prep.jpg"
        if os.path.exists(prep):
            os.remove(prep)

    return output_path
