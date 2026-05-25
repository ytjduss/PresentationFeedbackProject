import json
from pathlib import Path


def build_summary(
    speed_result,
    pause_issues,
    text_issues,
    content_result,
    gaze_result,
    gesture_result
):
    filler_count = sum(1 for issue in text_issues if issue["type"] == "filler")
    repeat_count = sum(1 for issue in text_issues if issue["type"] == "repeat")
    stutter_count = sum(1 for issue in text_issues if issue["type"] == "stutter")

    hesitation_count = sum(1 for issue in pause_issues if issue["type"] == "hesitation")
    pause_count = sum(1 for issue in pause_issues if issue["type"] == "pause")

    gaze_issue_count = len(gaze_result["issues"])
    gesture_issue_count = len(gesture_result["issues"])

    total_issue_count = (
        filler_count
        + repeat_count
        + stutter_count
        + hesitation_count
        + pause_count
        + gaze_issue_count
        + gesture_issue_count
    )

    feedback_list = [
        speed_result["feedback"],
        content_result["contentFeedback"],
        gaze_result["summary"]["feedback"],
        gesture_result["summary"]["feedback"]
    ]

    return {
        "totalIssueCount": total_issue_count,

        "speechSpeed": speed_result,

        "fillerCount": filler_count,
        "repeatCount": repeat_count,
        "stutterCount": stutter_count,

        "hesitationCount": hesitation_count,
        "pauseCount": pause_count,

        "gaze": gaze_result["summary"],
        "gesture": gesture_result["summary"],
        "content": content_result,

        "overallFeedback": " ".join(feedback_list)
    }


def build_final_result(
    video_path,
    wav_path,
    stt_result,
    speed_result,
    pause_issues,
    text_issues,
    voice_density,
    content_result,
    gaze_result,
    gesture_result
):
    timeline_issues = []
    timeline_issues.extend(pause_issues)
    timeline_issues.extend(text_issues)
    timeline_issues.extend(gaze_result["issues"])
    timeline_issues.extend(gesture_result["issues"])

    timeline_issues.sort(key=lambda issue: issue["start"])

    summary = build_summary(
        speed_result=speed_result,
        pause_issues=pause_issues,
        text_issues=text_issues,
        content_result=content_result,
        gaze_result=gaze_result,
        gesture_result=gesture_result
    )

    return {
        "videoFile": str(video_path),
        "wavFile": str(wav_path),
        "sttText": stt_result["text"],
        "summary": summary,
        "timelineIssues": timeline_issues,
        "voiceDensity": voice_density,
        "segments": stt_result["segments"]
    }


def save_final_result(result, output_dir, video_path):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = Path(video_path)
    json_path = output_dir / f"{video_path.stem}_final_analysis.json"

    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return json_path