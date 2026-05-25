import re
from pathlib import Path
from pydub import AudioSegment, silence


def format_time(seconds):
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def extract_audio(video_path, output_dir):
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_path = output_dir / f"{video_path.stem}.wav"

    audio = AudioSegment.from_file(video_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    return wav_path


def count_korean_syllables(text):
    return len(re.findall(r"[가-힣]", text))


def analyze_speech_speed(text, wav_path):
    audio = AudioSegment.from_file(wav_path)
    duration_sec = len(audio) / 1000

    syllable_count = count_korean_syllables(text)
    word_count = len(text.split())

    if duration_sec == 0:
        syllables_per_sec = 0
        words_per_minute = 0
    else:
        syllables_per_sec = syllable_count / duration_sec
        words_per_minute = word_count / duration_sec * 60

    if syllables_per_sec < 2.5:
        speed_label = "느림"
        feedback = "말 속도가 느린 편입니다. 발표 흐름이 늘어질 수 있습니다."
    elif syllables_per_sec <= 4.0:
        speed_label = "적절"
        feedback = "말 속도가 비교적 적절합니다."
    else:
        speed_label = "빠름"
        feedback = "말 속도가 빠른 편입니다. 청자가 내용을 따라가기 어려울 수 있습니다."

    return {
        "durationSec": round(duration_sec, 2),
        "wordCount": word_count,
        "syllableCount": syllable_count,
        "syllablesPerSec": round(syllables_per_sec, 2),
        "wordsPerMinute": round(words_per_minute, 2),
        "speedLabel": speed_label,
        "feedback": feedback
    }


def detect_pauses(wav_path):
    audio = AudioSegment.from_file(wav_path)

    silence_thresh = audio.dBFS - 14

    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=250,
        silence_thresh=silence_thresh
    )

    issues = []

    for start_ms, end_ms in silent_ranges:
        start = start_ms / 1000
        end = end_ms / 1000
        duration = end - start

        if duration < 0.25:
            continue

        if start < 0.3:
            continue

        if duration >= 0.8:
            issue_type = "pause"
            label = "긴 침묵"
            message = f"{duration:.1f}초 동안 말이 멈췄습니다."
        else:
            issue_type = "hesitation"
            label = "짧은 발화 끊김"
            message = f"{duration:.1f}초 정도 발화가 끊겼습니다."

        issues.append({
            "type": issue_type,
            "category": "audio",
            "label": label,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(duration, 2),
            "time": format_time(start),
            "message": message
        })

    return issues


def analyze_voice_density(wav_path, window_sec=5):
    audio = AudioSegment.from_file(wav_path)
    total_ms = len(audio)
    window_ms = window_sec * 1000
    silence_thresh = audio.dBFS - 14

    results = []

    for start_ms in range(0, total_ms, window_ms):
        end_ms = min(start_ms + window_ms, total_ms)
        chunk = audio[start_ms:end_ms]

        silent_ranges = silence.detect_silence(
            chunk,
            min_silence_len=250,
            silence_thresh=silence_thresh
        )

        silent_ms = sum(end - start for start, end in silent_ranges)
        chunk_duration_ms = end_ms - start_ms
        speaking_ms = chunk_duration_ms - silent_ms

        if chunk_duration_ms == 0:
            speaking_ratio = 0
        else:
            speaking_ratio = speaking_ms / chunk_duration_ms

        start_sec = start_ms / 1000
        end_sec = end_ms / 1000

        if speaking_ratio < 0.35:
            label = "발화 적음"
            feedback = "이 구간은 말소리보다 침묵이 많습니다."
        elif speaking_ratio < 0.55:
            label = "발화 흐름 약함"
            feedback = "이 구간은 발화가 다소 끊기는 편입니다."
        else:
            label = "발화 안정"
            feedback = "이 구간은 발화가 비교적 안정적입니다."

        results.append({
            "start": round(start_sec, 2),
            "end": round(end_sec, 2),
            "time": format_time(start_sec),
            "speakingRatio": round(speaking_ratio, 2),
            "label": label,
            "feedback": feedback
        })

    return results