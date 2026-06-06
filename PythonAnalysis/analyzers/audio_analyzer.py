import os
import re
import wave
import tempfile
import subprocess
import numpy as np
import whisper

FILLER_WORDS = [
    "어", "음", "아", "그", "그니까", "그러니까",
    "이제", "약간", "뭔가", "일단", "사실"
]

def analyze_audio(video_path, model_name="base"):
    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = os.path.join(temp_dir, "audio.wav")

        try:
            extract_audio(video_path, wav_path)
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

        duration = get_wav_duration(wav_path)
        silence_result = detect_silence(wav_path)

        try:
            transcript = transcribe_audio(wav_path, model_name)
        except Exception as e:
            transcript = ""
            whisper_error = str(e)
        else:
            whisper_error = None

        word_count = estimate_word_count(transcript)
        speech_rate = calculate_wpm(word_count, duration)
        filler_result = count_fillers(transcript)

        return {
            "available": True,
            "duration_sec": round(duration, 2),
            "transcript": transcript,
            "word_count": word_count,
            "speech_rate_wpm": round(speech_rate, 1),
            "filler_count": filler_result["total"],
            "filler_detail": filler_result["detail"],
            "silence": silence_result,
            "whisper_error": whisper_error
        }

def extract_audio(video_path, wav_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        wav_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("ffmpeg 음성 추출 실패")

def transcribe_audio(wav_path, model_name="base"):
    model = whisper.load_model(model_name)
    result = model.transcribe(wav_path, fp16=False)
    return result["text"].strip()

def get_wav_duration(wav_path):
    with wave.open(wav_path, "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        return frames / float(rate)

def detect_silence(wav_path, threshold=0.015, min_silence_sec=0.8):
    with wave.open(wav_path, "rb") as wav:
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    window_size = int(sample_rate * 0.1)
    silent_windows = []

    for i in range(0, len(audio), window_size):
        chunk = audio[i:i + window_size]

        if len(chunk) == 0:
            continue

        rms = np.sqrt(np.mean(chunk ** 2))
        silent_windows.append(rms < threshold)

    silence_segments = []
    start = None

    for i, is_silent in enumerate(silent_windows):
        current_time = i * 0.1

        if is_silent and start is None:
            start = current_time

        if not is_silent and start is not None:
            end = current_time

            if end - start >= min_silence_sec:
                silence_segments.append({
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "duration": round(end - start, 2)
                })

            start = None

    total_silence = sum(segment["duration"] for segment in silence_segments)

    return {
        "silence_count": len(silence_segments),
        "total_silence_sec": round(total_silence, 2),
        "segments": silence_segments[:10]
    }

def estimate_word_count(text):
    korean_count = len(re.findall(r"[가-힣]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    korean_words = int(korean_count / 2.5)

    return korean_words + english_words

def calculate_wpm(word_count, duration_sec):
    if duration_sec <= 0:
        return 0

    minutes = duration_sec / 60

    return word_count / minutes

def count_fillers(text):
    detail = {}
    total = 0

    for word in FILLER_WORDS:
        count = text.count(word)

        if count > 0:
            detail[word] = count
            total += count

    return {
        "total": total,
        "detail": detail
    }
