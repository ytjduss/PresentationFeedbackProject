import json
import subprocess
import sys
from pathlib import Path
from pydub import AudioSegment, silence
import whisper

###
# 1. 영상 파일 존재 확인
# 2. mp4 → wav 음성 추출
# 3. Whisper STT
# 4. 말 속도 분석
# 5. 간투사 탐지: 어, 음, 그, 저 등
# 6. 반복/더듬음 의심 탐지
# 7. 긴 침묵 탐지
# 8. txt/json 결과 저장
# 9. 타임라인용 issue 목록 생성
# ###

import sys
import json
import re
from pathlib import Path

import whisper
from pydub import AudioSegment, silence


# =========================
# 설정값
# =========================

FILLER_WORDS = {
    "어", "음", "그", "저", "아", "에",
    "어음", "으음", "음음", "그그"
}

MIN_SILENCE_LEN_MS = 700       # 0.7초 이상 조용하면 침묵으로 판단
SILENCE_OFFSET_DB = 16         # 전체 dBFS 기준으로 침묵 임계값 계산


# =========================
# 유틸 함수
# =========================

def format_time(seconds):
    seconds = float(seconds)
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def clean_word(word):
    return word.strip(".,!?…~\"'“”‘’()[]{}<> \n\t")


def count_korean_syllables(text):
    """
    한글 음절 개수 대략 계산.
    말속도 계산용.
    """
    return len(re.findall(r"[가-힣]", text))


def safe_mkdir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


# =========================
# 1. 영상에서 음성 추출
# =========================

def extract_audio(video_path, output_dir):
    video_path = Path(video_path)
    output_dir = safe_mkdir(output_dir)

    audio_path = output_dir / f"{video_path.stem}.wav"

    print("[1] 영상에서 음성 추출 중...")
    audio = AudioSegment.from_file(video_path)

    # Whisper에 맞게 mono, 16kHz로 변환
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(audio_path, format="wav")

    print(f"    저장 완료: {audio_path}")
    return audio_path


# =========================
# 2. Whisper STT
# =========================

def transcribe_audio(audio_path, model_name="small"):
    audio_path = Path(audio_path)

    print("[2] Whisper 모델 로딩 중...")
    model = whisper.load_model(model_name)

    print("[3] STT 분석 중...")
    result = model.transcribe(
        str(audio_path),
        language="ko",
        fp16=False,
        temperature=0,
        condition_on_previous_text=False,
        word_timestamps=False
    )

    text = result.get("text", "").strip()
    segments = result.get("segments", [])

    return {
        "text": text,
        "segments": segments
    }


# =========================
# 3. 간투사 탐지
# =========================

def detect_fillers_in_segment(text, start, end):
    words = text.split()
    issues = []

    for word in words:
        cleaned = clean_word(word)

        if cleaned in FILLER_WORDS:
            issues.append({
                "type": "filler",
                "label": "간투사",
                "text": cleaned,
                "start": start,
                "end": end,
                "time": format_time(start),
                "message": f"간투사 사용: '{cleaned}'"
            })

    return issues


# =========================
# 4. 반복/더듬음 의심 탐지
# =========================

def detect_repetition_in_segment(text, start, end):
    words = [clean_word(w) for w in text.split()]
    words = [w for w in words if w]

    issues = []

    for i in range(len(words) - 1):
        current_word = words[i]
        next_word = words[i + 1]

        # 같은 단어 반복: 친구 친구
        if current_word == next_word:
            issues.append({
                "type": "repeat",
                "label": "반복 표현",
                "text": f"{current_word} {next_word}",
                "start": start,
                "end": end,
                "time": format_time(start),
                "message": f"같은 단어 반복 의심: '{current_word} {next_word}'"
            })

        # 첫 음절 더듬음: 마 마지막으로, 성 성격과
        elif len(current_word) >= 1 and len(next_word) >= 2:
            if next_word.startswith(current_word):
                issues.append({
                    "type": "stutter",
                    "label": "더듬음 의심",
                    "text": f"{current_word} {next_word}",
                    "start": start,
                    "end": end,
                    "time": format_time(start),
                    "message": f"더듬음 의심: '{current_word} {next_word}'"
                })

        # 앞 단어가 다음 단어의 첫 글자와 같은 경우: 마 마지막으로
        if len(current_word) == 1 and len(next_word) >= 2:
            if next_word.startswith(current_word):
                issues.append({
                    "type": "stutter",
                    "label": "더듬음 의심",
                    "text": f"{current_word} {next_word}",
                    "start": start,
                    "end": end,
                    "time": format_time(start),
                    "message": f"첫 음절 반복 의심: '{current_word} {next_word}'"
                })

    return issues


# =========================
# 5. 침묵 탐지
# =========================

def detect_silence_ranges(audio_path):
    audio_path = Path(audio_path)

    print("[4] 침묵 구간 분석 중...")
    audio = AudioSegment.from_file(audio_path)

    silence_thresh = audio.dBFS - SILENCE_OFFSET_DB

    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=silence_thresh
    )

    issues = []

    for start_ms, end_ms in silent_ranges:
        start = start_ms / 1000
        end = end_ms / 1000
        duration = end - start

        issues.append({
            "type": "pause",
            "label": "긴 침묵",
            "text": "",
            "start": start,
            "end": end,
            "duration": duration,
            "time": format_time(start),
            "message": f"{duration:.1f}초 침묵"
        })

    return issues


# =========================
# 6. 말 속도 분석
# =========================

def analyze_speech_speed(text, audio_path):
    audio = AudioSegment.from_file(audio_path)
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
        "duration_sec": round(duration_sec, 2),
        "syllable_count": syllable_count,
        "word_count": word_count,
        "syllables_per_sec": round(syllables_per_sec, 2),
        "words_per_minute": round(words_per_minute, 2),
        "speed_label": speed_label,
        "feedback": feedback
    }


# =========================
# 7. 전체 발화 흐름 분석
# =========================

def analyze_fluency(stt_result, audio_path):
    text = stt_result["text"]
    segments = stt_result["segments"]

    issues = []

    print("[5] 간투사/반복/더듬음 의심 분석 중...")

    for segment in segments:
        segment_text = segment.get("text", "").strip()
        start = segment.get("start", 0)
        end = segment.get("end", 0)

        issues.extend(detect_fillers_in_segment(segment_text, start, end))
        issues.extend(detect_repetition_in_segment(segment_text, start, end))

    pause_issues = detect_silence_ranges(audio_path)
    issues.extend(pause_issues)

    issues.sort(key=lambda x: x["start"])

    filler_count = sum(1 for issue in issues if issue["type"] == "filler")
    repeat_count = sum(1 for issue in issues if issue["type"] == "repeat")
    stutter_count = sum(1 for issue in issues if issue["type"] == "stutter")
    pause_count = sum(1 for issue in issues if issue["type"] == "pause")

    speed_result = analyze_speech_speed(text, audio_path)

    total_issue_count = filler_count + repeat_count + stutter_count + pause_count

    if total_issue_count <= 3:
        overall_feedback = "발화 흐름이 안정적인 편입니다."
    elif total_issue_count <= 10:
        overall_feedback = "일부 구간에서 발화 흐름이 끊기거나 반복되는 부분이 있습니다."
    else:
        overall_feedback = "간투사, 반복, 침묵이 많아 발표 전달력이 떨어질 수 있습니다."

    return {
        "summary": {
            "total_issue_count": total_issue_count,
            "filler_count": filler_count,
            "repeat_count": repeat_count,
            "stutter_count": stutter_count,
            "pause_count": pause_count,
            "speech_speed": speed_result,
            "overall_feedback": overall_feedback
        },
        "issues": issues
    }


# =========================
# 8. 결과 저장
# =========================

def save_results(video_path, output_dir, stt_result, fluency_result):
    video_path = Path(video_path)
    output_dir = safe_mkdir(output_dir)

    txt_path = output_dir / f"{video_path.stem}_stt.txt"
    json_path = output_dir / f"{video_path.stem}_analysis.json"

    txt_path.write_text(stt_result["text"], encoding="utf-8")

    final_result = {
        "video_file": str(video_path),
        "stt_text": stt_result["text"],
        "segments": stt_result["segments"],
        "fluency_analysis": fluency_result
    }

    json_path.write_text(
        json.dumps(final_result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("[6] 결과 저장 완료")
    print(f"    STT 텍스트: {txt_path}")
    print(f"    분석 JSON: {json_path}")

    return txt_path, json_path


# =========================
# 9. 콘솔 출력
# =========================

def print_summary(fluency_result):
    summary = fluency_result["summary"]
    speed = summary["speech_speed"]

    print("\n==============================")
    print("발표 분석 결과")
    print("==============================")
    print(f"전체 문제 감지 수: {summary['total_issue_count']}")
    print(f"간투사: {summary['filler_count']}회")
    print(f"반복 표현: {summary['repeat_count']}회")
    print(f"더듬음 의심: {summary['stutter_count']}회")
    print(f"긴 침묵: {summary['pause_count']}회")
    print()
    print(f"발표 길이: {speed['duration_sec']}초")
    print(f"음절 수: {speed['syllable_count']}개")
    print(f"단어 수: {speed['word_count']}개")
    print(f"말 속도: {speed['syllables_per_sec']} 음절/초")
    print(f"분당 단어 수: {speed['words_per_minute']} WPM")
    print(f"속도 평가: {speed['speed_label']}")
    print(f"속도 피드백: {speed['feedback']}")
    print()
    print(f"종합 피드백: {summary['overall_feedback']}")

    print("\n==============================")
    print("타임라인 이슈")
    print("==============================")

    issues = fluency_result["issues"]

    if not issues:
        print("감지된 이슈가 없습니다.")
        return

    for issue in issues:
        print(f"[{issue['time']}] {issue['label']} - {issue['message']}")


# =========================
# 10. 실행 함수
# =========================

def run(video_file, model_name="small"):
    video_path = Path(video_file)

    if not video_path.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")

    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"

    audio_path = extract_audio(video_path, output_dir)
    stt_result = transcribe_audio(audio_path, model_name)
    fluency_result = analyze_fluency(stt_result, audio_path)

    save_results(video_path, output_dir, stt_result, fluency_result)
    print_summary(fluency_result)


# =========================
# 11. main
# =========================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python speech_to_text.py <video_path> [model_name]")
        print()
        print("예시:")
        print("python speech_to_text.py ../input/A00_S01_F_F_03_089_02_WA_MO.mp4 small")
        sys.exit(1)

    video_file = sys.argv[1]

    if len(sys.argv) >= 3:
        model_name = sys.argv[2]
    else:
        model_name = "small"

    run(video_file, model_name)