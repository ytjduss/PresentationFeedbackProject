import json
import sys
from pathlib import Path

from PythonAnalysis.analyzers.audio_analyzer import analyze_audio
from PythonAnalysis.analyzers.feedback_generator import generate_feedback
from PythonAnalysis.analyzers.video_analyzer import analyze_video


def run(video_path, model_name="base"):
    video_file = Path(video_path)

    if not video_file.exists():
        return {
            "success": False,
            "error": f"영상 파일을 찾을 수 없습니다: {video_path}"
        }

    video_result = analyze_video(video_path)
    audio_result = analyze_audio(video_path, model_name)

    if not video_result.get("available") and not audio_result.get("available"):
        return {
            "success": False,
            "error": "영상과 음성 분석을 모두 수행하지 못했습니다.",
            "video": video_result,
            "audio": audio_result
        }

    feedback = generate_feedback(video_result, audio_result)

    return {
        "success": True,
        "video": video_result,
        "audio": audio_result,
        "feedback": feedback
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "영상 파일 경로가 필요합니다."
        }, ensure_ascii=False))
        return

    video_path = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) >= 3 else "base"

    result = run(video_path, model_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
