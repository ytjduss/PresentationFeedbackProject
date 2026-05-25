import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from PythonAnalysis.audio_analyser import extract_audio, analyze_speech_speed, detect_pauses, analyze_voice_density
#from PythonAnalysis.result_builder import build_result
from PythonAnalysis.speech_analyser import transcribe_audio, detect_text_issues
from PythonAnalysis.content_analyzer import analyze_content
from PythonAnalysis.gaze_analyzer import analyze_gaze
from PythonAnalysis.gesture_analyzer import analyze_gesture
from PythonAnalysis.result_builder import (
    build_final_result,
    save_final_result
)


# from audio_analyzer import (
#     extract_audio,
#     analyze_speech_speed,
#     detect_pauses,
#     analyze_voice_density
# )
#
# from speech_analyzer import (
#     transcribe_audio,
#     detect_text_issues
# )


def print_summary(result):
    summary = result["summary"]

    print("\n==============================")
    print("최종 발표 분석 결과")
    print("==============================")

    print(f"전체 이슈 수: {summary['totalIssueCount']}")

    print("\n[말 빠르기]")
    print(f"발표 길이: {summary['speechSpeed']['durationSec']}초")
    print(f"단어 수: {summary['speechSpeed']['wordCount']}개")
    print(f"음절 수: {summary['speechSpeed']['syllableCount']}개")
    print(f"말 속도: {summary['speechSpeed']['syllablesPerSec']} 음절/초")
    print(f"속도 평가: {summary['speechSpeed']['speedLabel']}")

    print("\n[침묵구간]")
    print(f"짧은 발화 끊김: {summary['hesitationCount']}회")
    print(f"긴 침묵: {summary['pauseCount']}회")

    print("\n[발표 내용]")
    print(f"문장 수: {summary['content']['sentenceCount']}개")
    print(f"내용 평가: {summary['content']['contentFeedback']}")
    print("핵심 키워드:", end=" ")

    keywords = summary["content"]["keywords"]
    keyword_texts = [item["keyword"] for item in keywords]
    print(", ".join(keyword_texts))

    print("\n[시선처리]")
    print(f"정면 비율: {summary['gaze']['frontRatio']}")
    print(f"왼쪽 비율: {summary['gaze']['leftRatio']}")
    print(f"오른쪽 비율: {summary['gaze']['rightRatio']}")
    print(f"시선 피드백: {summary['gaze']['feedback']}")

    print("\n[손동작]")
    print(f"손동작 수준: {summary['gesture']['gestureLevel']}")
    print(f"손동작 부족 구간: {summary['gesture']['lowGestureCount']}회")
    print(f"손동작 피드백: {summary['gesture']['feedback']}")

    print("\n[종합 피드백]")
    print(summary["overallFeedback"])

    print("\n==============================")
    print("타임라인 이슈")
    print("==============================")

    for issue in result["timelineIssues"]:
        print(f"[{issue['time']}] {issue['label']} - {issue['message']}")


def run(video_file, model_name="small"):
    video_path = Path(video_file)

    if not video_path.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")

    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"

    print("[1] WAV 음성 추출")
    wav_path = extract_audio(video_path, output_dir)

    print("[2] Whisper STT 변환")
    stt_result = transcribe_audio(wav_path, model_name)

    print("[3] 말 빠르기 분석")
    speed_result = analyze_speech_speed(stt_result["text"], wav_path)

    print("[4] 침묵구간 분석")
    pause_issues = detect_pauses(wav_path)

    print("[5] 발화 밀도 분석")
    voice_density = analyze_voice_density(wav_path, window_sec=5)

    print("[6] 발표 내용 분석")
    content_result = analyze_content(stt_result["text"])

    print("[7] STT 텍스트 기반 간투사/반복 분석")
    text_issues = detect_text_issues(stt_result["segments"])

    print("[8] 시선처리 분석")
    gaze_result = analyze_gaze(video_path, sample_every_sec=1.0)

    print("[9] 손동작 분석")
    gesture_result = analyze_gesture(video_path, sample_every_sec=0.5)

    print("[10] 최종 JSON 생성")
    final_result = build_final_result(
        video_path=video_path,
        wav_path=wav_path,
        stt_result=stt_result,
        speed_result=speed_result,
        pause_issues=pause_issues,
        text_issues=text_issues,
        voice_density=voice_density,
        content_result=content_result,
        gaze_result=gaze_result,
        gesture_result=gesture_result
    )

    json_path = save_final_result(final_result, output_dir, video_path)

    print_summary(final_result)

    print("\n==============================")
    print("저장 완료")
    print("==============================")
    print(f"최종 분석 JSON: {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("python main_analysis.py <video_path> [model_name]")
        print()
        print("예시:")
        print("python main_analysis.py ../input/A00_S01_F_F_03_089_02_WA_MO.mp4 small")
        sys.exit(1)

    video_file = sys.argv[1]

    if len(sys.argv) >= 3:
        model_name = sys.argv[2]
    else:
        model_name = "small"

    run(video_file, model_name)
