import json
import subprocess
import sys
from pathlib import Path
from pydub import AudioSegment, silence
import pyaudioop as audioop
import whisper


def extract_audio(video_path: Path, output_dir: Path) -> Path:
    """
    동영상 파일에서 음성을 WAV 파일로 추출한다.
    Whisper 입력에 맞게 16kHz, mono 형식으로 변환한다.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"{video_path.stem}.wav"
    fluency_result = analyze_fluency(Path(audio_path))
    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 음성 추출 실패:\n{result.stderr}")

    return audio_path


def transcribe_audio(audio_path: Path, model_name: str = "small") -> dict:
    """
    Whisper를 사용해 한국어 음성을 텍스트로 변환한다.
    model_name: tiny, base, small, medium 중 선택 가능
    """
    model = whisper.load_model(model_name)

    result = model.transcribe(
        str(audio_path),
        language="ko",
        task="transcribe",
        fp16=False
    )

    return result


def save_transcript(result: dict, output_dir: Path, base_name: str) -> tuple[Path, Path]:
    """
    전체 텍스트와 구간별 텍스트를 파일로 저장한다.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = output_dir / f"{base_name}_transcript.txt"
    json_path = output_dir / f"{base_name}_speech_result.json"

    text = result.get("text", "").strip()
    segments = result.get("segments", [])

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    segment_data = []

    for segment in segments:
        segment_data.append({
            "start": round(segment["start"], 2),
            "end": round(segment["end"], 2),
            "text": segment["text"].strip()
        })

    output_data = {
        "transcript": text,
        "segments": segment_data
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return transcript_path, json_path


def run(video_file: str, model_name: str = "small") -> None:
    video_path = Path(video_file)

    if not video_path.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")

    output_dir = Path("output")

    print("[1/3] 음성 추출 중...")
    audio_path = extract_audio(video_path, output_dir)
    print(f"음성 파일 생성 완료: {audio_path}")

    print("[2/3] 한국어 음성 인식 중...")
    result = transcribe_audio(audio_path, model_name=model_name)

    print("[3/3] 결과 저장 중...")
    transcript_path, json_path = save_transcript(result, output_dir, video_path.stem)

    print("완료")
    print(f"텍스트 파일: {transcript_path}")
    print(f"JSON 파일: {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python speech_to_text.py 영상파일경로 [모델명]")
        print("예시:")
        print("python speech_to_text.py input/presentation.mp4 small")
        sys.exit(1)

    video_file = sys.argv[1]

    if len(sys.argv) >= 3:
        model_name = sys.argv[2]
    else:
        model_name = "small"

    run(video_file, model_name)


    def analyze_fluency(audio_path: Path) -> dict:
        audio = AudioSegment.from_wav(audio_path)

        duration_sec = len(audio) / 1000

        # 침묵 구간 탐지
        silent_ranges = silence.detect_silence(
            audio,
            min_silence_len=500,  # 0.5초 이상 조용하면 침묵
            silence_thresh=audio.dBFS - 16
        )

        # ms → sec 변환
        silence_segments = [
            {
                "start": round(start / 1000, 2),
                "end": round(end / 1000, 2),
                "duration": round((end - start) / 1000, 2)
            }
            for start, end in silent_ranges
        ]

        long_silences = [
            seg for seg in silence_segments
            if seg["duration"] >= 1.0
        ]

        short_breaks = [
            seg for seg in silence_segments
            if 0.5 <= seg["duration"] < 1.0
        ]

        silence_count = len(silence_segments)
        long_silence_count = len(long_silences)
        short_break_count = len(short_breaks)

        # 유창성 점수 계산
        fluency_score = 100

        fluency_score -= long_silence_count * 6
        fluency_score -= short_break_count * 2

        if silence_count > duration_sec / 8:
            fluency_score -= 10

        fluency_score = max(0, min(100, fluency_score))

        if fluency_score >= 85:
            feedback = "발화 흐름이 안정적입니다."
        elif fluency_score >= 70:
            feedback = "중간중간 짧은 끊김이 감지되었습니다. 문장 시작 전 호흡을 정리하면 더 자연스럽습니다."
        else:
            feedback = "발화 중 끊김과 긴 침묵이 자주 나타났습니다. 문장을 짧게 나누어 말하는 연습이 필요합니다."

        return {
            "fluencyScore": fluency_score,
            "silenceCount": silence_count,
            "longSilenceCount": long_silence_count,
            "shortBreakCount": short_break_count,
            "silenceSegments": silence_segments,
            "fluencyFeedback": feedback
        }