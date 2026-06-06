def generate_feedback(video, audio):
    video_available = video.get("available", False)
    audio_available = audio.get("available", False)

    scores = {
        "eye_contact": score_eye_contact(video),
        "gesture": score_gesture(video),
        "posture": score_posture(video),
        "speech_rate": score_speech_rate(audio),
        "filler": score_filler(audio),
        "silence": score_silence(audio)
    }

    total_score = sum(scores.values())

    strengths = []
    improvements = []

    eye_rate = video.get("eye_contact_rate", 0)
    gesture_rate = video.get("gesture_rate", 0)
    posture_rate = video.get("posture_stability_rate", 0)
    eye_available = video.get("eye_contact_available", False)
    gesture_available = video.get("gesture_available", False)
    posture_available = video.get("posture_available", False)

    speech_rate = audio.get("speech_rate_wpm", 0)
    filler_count = audio.get("filler_count", 0)
    silence_count = audio.get("silence", {}).get("silence_count", 0)

    if not video_available:
        improvements.append("영상 분석을 수행하지 못해 시선, 제스처, 자세 평가는 제외되었습니다.")
    else:
        if not eye_available:
            improvements.append("얼굴이 충분히 감지되지 않아 시선 평가는 제외되었습니다.")
        elif eye_rate >= 0.6:
            strengths.append("시선 처리가 안정적입니다.")
        else:
            improvements.append("카메라나 청중을 바라보는 시간이 부족합니다.")

        if not gesture_available:
            improvements.append("상체 관절이 충분히 감지되지 않아 손동작 평가는 제외되었습니다.")
        elif 0.2 <= gesture_rate <= 0.7:
            strengths.append("제스처 사용이 자연스럽습니다.")
        elif gesture_rate < 0.2:
            improvements.append("손동작이 부족해 발표가 다소 정적으로 보일 수 있습니다.")
        else:
            improvements.append("제스처가 많아 발표가 산만해 보일 수 있습니다.")

        if not posture_available:
            improvements.append("상체 관절이 충분히 감지되지 않아 자세 평가는 제외되었습니다.")
        elif posture_rate >= 0.6:
            strengths.append("자세가 비교적 안정적입니다.")
        else:
            improvements.append("어깨 기울기나 자세 흔들림이 감지되었습니다.")

    if not audio_available:
        improvements.append("음성 분석을 수행하지 못해 말 빠르기, 습관어, 침묵 평가는 제외되었습니다.")
    else:
        if 120 <= speech_rate <= 170:
            strengths.append("발표 속도가 적절합니다.")
        elif speech_rate < 120:
            improvements.append("발표 속도가 느린 편입니다.")
        else:
            improvements.append("발표 속도가 빠른 편입니다.")

        if filler_count <= 5:
            strengths.append("습관어 사용이 적은 편입니다.")
        else:
            improvements.append("‘어’, ‘음’, ‘그니까’ 같은 습관어를 줄이면 좋습니다.")

        if silence_count <= 3:
            strengths.append("침묵 구간이 과하지 않습니다.")
        else:
            improvements.append("긴 침묵이 반복되어 발표 흐름이 끊길 수 있습니다.")

    return {
        "total_score": total_score,
        "grade": get_grade(total_score),
        "scores": scores,
        "strengths": strengths,
        "improvements": improvements,
        "one_line_feedback": make_one_line_feedback(total_score, improvements)
    }

def score_eye_contact(video):
    if not video.get("available", False) or not video.get("eye_contact_available", False):
        return 0

    rate = video.get("eye_contact_rate", 0)

    if rate >= 0.75:
        return 20
    if rate >= 0.55:
        return 16
    if rate >= 0.35:
        return 11
    return 6

def score_gesture(video):
    if not video.get("available", False) or not video.get("gesture_available", False):
        return 0

    rate = video.get("gesture_rate", 0)

    if 0.25 <= rate <= 0.65:
        return 15
    if 0.15 <= rate < 0.25 or 0.65 < rate <= 0.8:
        return 11
    return 7

def score_posture(video):
    if not video.get("available", False) or not video.get("posture_available", False):
        return 0

    rate = video.get("posture_stability_rate", 0)

    if rate >= 0.75:
        return 15
    if rate >= 0.55:
        return 11
    return 7

def score_speech_rate(audio):
    if not audio.get("available", False):
        return 0

    wpm = audio.get("speech_rate_wpm", 0)

    if 120 <= wpm <= 170:
        return 20
    if 100 <= wpm < 120 or 170 < wpm <= 190:
        return 15
    return 8

def score_filler(audio):
    if not audio.get("available", False):
        return 0

    count = audio.get("filler_count", 0)

    if count <= 3:
        return 15
    if count <= 7:
        return 11
    return 6

def score_silence(audio):
    if not audio.get("available", False):
        return 0

    count = audio.get("silence", {}).get("silence_count", 0)

    if count <= 2:
        return 15
    if count <= 5:
        return 10
    return 5

def get_grade(score):
    if score >= 85:
        return "우수"
    if score >= 70:
        return "보통 이상"
    if score >= 55:
        return "보완 필요"
    return "집중 개선 필요"

def make_one_line_feedback(score, improvements):
    if not improvements:
        return "전반적으로 안정적인 발표입니다."

    if score >= 70:
        return "전체 흐름은 좋지만, " + improvements[0]

    return "발표 완성도를 높이기 위해 " + improvements[0]
