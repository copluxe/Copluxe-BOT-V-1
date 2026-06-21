import os
import random
import numpy as np
from scipy.io import wavfile
from typing import Optional

MUSIC_DIR = os.getenv("MUSIC_DIR", "./assets/music")

# Music metadata: maps style tags to BPM and energy
MUSIC_CATALOG = [
    {"file": "hype_001.wav", "tags": ["hype", "fast", "energetic", "drop"], "bpm": 135, "energy": "high"},
    {"file": "hype_002.wav", "tags": ["hype", "fire", "trending", "lit"], "bpm": 128, "energy": "high"},
    {"file": "luxury_001.wav", "tags": ["luxury", "elegant", "premium", "sophisticated"], "bpm": 75, "energy": "low"},
    {"file": "luxury_002.wav", "tags": ["luxury", "exclusive", "prestige"], "bpm": 80, "energy": "low"},
    {"file": "california_001.wav", "tags": ["california", "summer", "beach", "chill", "vibes"], "bpm": 95, "energy": "medium"},
    {"file": "fashion_001.wav", "tags": ["fashion", "style", "trendy", "collection"], "bpm": 110, "energy": "medium"},
    {"file": "trap_001.wav", "tags": ["hype", "trap", "street", "urban", "swag"], "bpm": 140, "energy": "high"},
    {"file": "chill_001.wav", "tags": ["chill", "relax", "smooth", "laid-back"], "bpm": 85, "energy": "low"},
]

STYLE_TO_TAGS = {
    "luxury": ["luxury", "elegant", "premium"],
    "hype": ["hype", "fire", "energetic", "drop"],
    "california": ["california", "summer", "chill"],
    "fashion": ["fashion", "style"],
    "sport": ["energetic", "hype", "fast"],
    "fast": ["hype", "fast", "trap"],
    "default": ["fashion", "style"],
}


def score_track(track: dict, description_lower: str, target_tags: list) -> int:
    score = 0
    for tag in track["tags"]:
        if tag in description_lower:
            score += 3
        if tag in target_tags:
            score += 2
    return score


def select_music(description: str, style: str = "default") -> Optional[str]:
    desc_lower = description.lower()
    target_tags = STYLE_TO_TAGS.get(style, STYLE_TO_TAGS["default"])

    # Score all tracks
    scored = [(score_track(t, desc_lower, target_tags), t) for t in MUSIC_CATALOG]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Try to find an existing file, highest score first
    for score, track in scored:
        path = os.path.join(MUSIC_DIR, track["file"])
        if os.path.exists(path):
            return path

    # No music files found; generate synthetic audio
    return generate_synthetic_music(style, duration=60)


def generate_synthetic_music(style: str = "default", duration: int = 60) -> Optional[str]:
    try:
        os.makedirs(MUSIC_DIR, exist_ok=True)
        output_path = os.path.join(MUSIC_DIR, f"generated_{style}.wav")

        if os.path.exists(output_path):
            return output_path

        sample_rate = 44100
        bpm_map = {"hype": 135, "luxury": 75, "california": 95, "fast": 140, "default": 110}
        bpm = bpm_map.get(style, 110)

        audio = _generate_beat(bpm, duration, sample_rate, style)

        # Normalize and convert to int16
        audio = audio / np.max(np.abs(audio) + 1e-8) * 0.7
        audio_int16 = (audio * 32767).astype(np.int16)

        # Stereo
        stereo = np.column_stack([audio_int16, audio_int16])
        wavfile.write(output_path, sample_rate, stereo)
        return output_path
    except Exception:
        return None


def _generate_beat(bpm: int, duration: int, sample_rate: int, style: str) -> np.ndarray:
    total_samples = sample_rate * duration
    audio = np.zeros(total_samples)

    beat_samples = int(sample_rate * 60 / bpm)
    half_beat = beat_samples // 2

    t_kick = np.linspace(0, 0.15, int(sample_rate * 0.15))
    kick = np.sin(2 * np.pi * 55 * t_kick * np.exp(-t_kick * 20)) * np.exp(-t_kick * 15)

    t_snare = np.linspace(0, 0.1, int(sample_rate * 0.1))
    snare = np.random.randn(len(t_snare)) * np.exp(-t_snare * 30) * 0.4

    # Bassline
    if style in ["hype", "fast"]:
        bass_freq = 80
    elif style == "luxury":
        bass_freq = 55
    else:
        bass_freq = 65

    for i in range(0, total_samples, beat_samples):
        # Kick on beats 1 and 3
        end = min(i + len(kick), total_samples)
        audio[i:end] += kick[:end - i] * 0.8

        # Snare on beats 2 and 4
        snare_pos = i + half_beat
        if snare_pos + len(snare) < total_samples:
            audio[snare_pos:snare_pos + len(snare)] += snare

        # Bass note
        bass_dur = int(sample_rate * 0.3)
        t_bass = np.linspace(0, 0.3, bass_dur)
        bass = np.sin(2 * np.pi * bass_freq * t_bass) * np.exp(-t_bass * 5) * 0.6
        end = min(i + bass_dur, total_samples)
        audio[i:end] += bass[:end - i]

    # Hi-hat
    hihat_interval = beat_samples // 4
    t_hat = np.linspace(0, 0.05, int(sample_rate * 0.05))
    hihat = np.random.randn(len(t_hat)) * np.exp(-t_hat * 80) * 0.2

    for i in range(0, total_samples, hihat_interval):
        end = min(i + len(hihat), total_samples)
        audio[i:end] += hihat[:end - i]

    # Smooth with slight reverb simulation
    reverb = np.convolve(audio, np.exp(-np.linspace(0, 3, sample_rate // 4)) * 0.1, mode='same')
    audio = audio + reverb * 0.15

    return audio
