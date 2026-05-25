import sys
import json
from pathlib import Path
from pydub import AudioSegment, silence


def format_time(seconds):
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def extract_audio_from_video(video_path, output_dir):
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_path = output_dir / f"{video_path.stem}.wav"

    audio = AudioSegment.from_file(video_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    return wav_path


def detect_voice_pauses(wav_path):
    """
    WAV 파형에서 조용한 구간을 찾는다.

    0.25초 ~ 0.8초  : 짧은 발화 끊김
    0.8초 이상     : 긴 침묵
    """

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

        # 영상 시작 직후/끝부분의 무음은 제외
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
            "label": label,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(duration, 2),
            "time": format_time(start),
            "message": message
        })

    return issues


def analyze_voice_activity_by_window(wav_path, window_sec=5):
    """
    5초 단위로 말소리가 얼마나 있는지 분석한다.
    말소리 비율이 낮으면 발표 흐름이 끊긴 구간으로 볼 수 있다.
    """

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

        silent_ms = 0

        for s, e in silent_ranges:
            silent_ms += e - s

        chunk_duration_ms = end_ms - start_ms
        speaking_ms = chunk_duration_ms - silent_ms

        if chunk_duration_ms == 0:
            speaking_ratio = 0
        else:
            speaking_ratio = speaking_ms / chunk_duration_ms

        start = start_ms / 1000
        end = end_ms / 1000

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
            "start": round(start, 2),
            "end": round(end, 2),
            "time": format_time(start),
            "window_sec": window_sec,
            "speaking_ratio": round(speaking_ratio, 2),
            "label": label,
            "feedback": feedback
        })

    return results


def summarize_pauses(issues):
    hesitation_count = sum(1 for issue in issues if issue["type"] == "hesitation")
    pause_count = sum(1 for issue in issues if issue["type"] == "pause")

    total_hesitation_time = sum(
        issue["duration"] for issue in issues
        if issue["type"] == "hesitation"
    )

    total_pause_time = sum(
        issue["duration"] for issue in issues
        if issue["type"] == "pause"
    )

    total_issue_count = hesitation_count + pause_count

    if total_issue_count <= 3:
        overall = "발화 흐름이 안정적인 편입니다."
    elif total_issue_count <= 10:
        overall = "중간중간 발화가 끊기는 구간이 있습니다."
    else:
        overall = "짧은 끊김과 침묵이 많아 발표 흐름이 불안정할 수 있습니다."

    return {
        "total_issue_count": total_issue_count,
        "hesitation_count": hesitation_count,
        "pause_count": pause_count,
        "total_hesitation_time": round(total_hesitation_time, 2),
        "total_pause_time": round(total_pause_time, 2),
        "overall_feedback": overall
    }


def save_result(output_dir, input_path, wav_path, issues, window_analysis, summary):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(input_path)

    result = {
        "input_file": str(input_path),
        "wav_file": str(wav_path),
        "summary": summary,
        "timeline_issues": issues,
        "window_analysis": window_analysis
    }

    json_path = output_dir / f"{input_path.stem}_wav_analysis.json"

    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return json_path


def print_result(summary, issues, window_analysis):
    print("\n==============================")
    print("WAV 파형 기반 발화 흐름 분석 결과")
    print("==============================")
    print(f"전체 이슈 수: {summary['total_issue_count']}")
    print(f"짧은 발화 끊김: {summary['hesitation_count']}회")
    print(f"긴 침묵: {summary['pause_count']}회")
    print(f"짧은 끊김 총 시간: {summary['total_hesitation_time']}초")
    print(f"긴 침묵 총 시간: {summary['total_pause_time']}초")
    print(f"종합 피드백: {summary['overall_feedback']}")

    print("\n==============================")
    print("타임라인 이슈")
    print("==============================")

    if not issues:
        print("감지된 침묵/끊김 구간이 없습니다.")
    else:
        for issue in issues:
            print(f"[{issue['time']}] {issue['label']} - {issue['message']}")

    print("\n==============================")
    print("5초 단위 발화 밀도")
    print("==============================")

    for item in window_analysis:
        print(
            f"[{item['time']}] "
            f"{item['label']} "
            f"- 발화 비율 {item['speaking_ratio']} "
            f"- {item['feedback']}"
        )


def run(input_file):
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_path}")

    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"

    if input_path.suffix.lower() == ".wav":
        wav_path = input_path
    else:
        print("[1] 영상에서 WAV 음성 추출 중...")
        wav_path = extract_audio_from_video(input_path, output_dir)
        print(f"    WAV 저장 완료: {wav_path}")

    print("[2] 짧은 끊김/긴 침묵 분석 중...")
    issues = detect_voice_pauses(wav_path)

    print("[3] 5초 단위 발화 밀도 분석 중...")
    window_analysis = analyze_voice_activity_by_window(wav_path, window_sec=5)

    summary = summarize_pauses(issues)

    json_path = save_result(
        output_dir=output_dir,
        input_path=input_path,
        wav_path=wav_path,
        issues=issues,
        window_analysis=window_analysis,
        summary=summary
    )

    print_result(summary, issues, window_analysis)

    print("\n==============================")
    print("저장 완료")
    print("==============================")
    print(f"분석 JSON: {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python wav_fluency_analysis.py <video_or_wav_path>")
        print()
        print("예시:")
        print("python wav_fluency_analysis.py ../input/A00_S01_F_F_03_089_02_WA_MO.mp4")
        print("python wav_fluency_analysis.py output/A00_S01_F_F_03_089_02_WA_MO.wav")
        sys.exit(1)

    run(sys.argv[1])