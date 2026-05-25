import cv2
import mediapipe as mp


def format_time(seconds):
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def get_direction(face_landmarks, width, height):
    landmarks = face_landmarks.landmark

    left_eye = landmarks[33]
    right_eye = landmarks[263]
    nose = landmarks[1]
    chin = landmarks[152]

    left_eye_x = left_eye.x * width
    right_eye_x = right_eye.x * width
    nose_x = nose.x * width

    eye_center_x = (left_eye_x + right_eye_x) / 2
    eye_distance = abs(right_eye_x - left_eye_x)

    nose_y = nose.y * height
    chin_y = chin.y * height

    # 좌우 판단
    x_offset = nose_x - eye_center_x

    if eye_distance == 0:
        return "unknown"

    x_ratio = x_offset / eye_distance

    # 아래를 보는 경우: 코가 턱 쪽으로 많이 내려간 것으로 단순 판단
    face_vertical = abs(chin_y - nose_y)

    if face_vertical < 30:
        return "unknown"

    if x_ratio > 0.18:
        return "right"
    elif x_ratio < -0.18:
        return "left"
    else:
        return "front"


def analyze_gaze(video_path, sample_every_sec=1.0):
    if not hasattr(mp, "solutions"):
        return analyze_gaze_with_opencv(video_path, sample_every_sec)

    mp_face_mesh = mp.solutions.face_mesh

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {
            "summary": {
                "frontRatio": 0,
                "leftRatio": 0,
                "rightRatio": 0,
                "noFaceRatio": 1,
                "feedback": "영상을 열 수 없어 시선 분석을 수행하지 못했습니다."
            },
            "issues": []
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        fps = 30

    frame_interval = max(1, int(fps * sample_every_sec))

    counts = {
        "front": 0,
        "left": 0,
        "right": 0,
        "unknown": 0,
        "no_face": 0
    }

    issues = []

    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        frame_idx = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            if frame_idx % frame_interval != 0:
                frame_idx += 1
                continue

            time_sec = frame_idx / fps

            height, width, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                counts["no_face"] += 1
                issues.append({
                    "type": "gaze_no_face",
                    "category": "gaze",
                    "label": "얼굴 미검출",
                    "start": round(time_sec, 2),
                    "end": round(time_sec + sample_every_sec, 2),
                    "time": format_time(time_sec),
                    "message": "얼굴이 감지되지 않았습니다."
                })
            else:
                direction = get_direction(
                    results.multi_face_landmarks[0],
                    width,
                    height
                )

                counts[direction] += 1

                if direction == "left":
                    issues.append({
                        "type": "gaze_left",
                        "category": "gaze",
                        "label": "왼쪽 시선",
                        "start": round(time_sec, 2),
                        "end": round(time_sec + sample_every_sec, 2),
                        "time": format_time(time_sec),
                        "message": "시선이 왼쪽으로 향한 것으로 추정됩니다."
                    })
                elif direction == "right":
                    issues.append({
                        "type": "gaze_right",
                        "category": "gaze",
                        "label": "오른쪽 시선",
                        "start": round(time_sec, 2),
                        "end": round(time_sec + sample_every_sec, 2),
                        "time": format_time(time_sec),
                        "message": "시선이 오른쪽으로 향한 것으로 추정됩니다."
                    })

            frame_idx += 1

    cap.release()

    total = sum(counts.values())

    if total == 0:
        total = 1

    front_ratio = counts["front"] / total
    left_ratio = counts["left"] / total
    right_ratio = counts["right"] / total
    no_face_ratio = counts["no_face"] / total

    if front_ratio >= 0.65:
        feedback = "정면 응시 비율이 높은 편입니다."
    elif front_ratio >= 0.4:
        feedback = "정면 응시가 일부 유지되지만, 시선 이탈 구간이 있습니다."
    else:
        feedback = "정면 응시 비율이 낮아 발표 집중도가 떨어져 보일 수 있습니다."

    return {
        "summary": {
            "frontRatio": round(front_ratio, 2),
            "leftRatio": round(left_ratio, 2),
            "rightRatio": round(right_ratio, 2),
            "noFaceRatio": round(no_face_ratio, 2),
            "sampleCount": total,
            "feedback": feedback
        },
        "issues": issues
    }


def analyze_gaze_with_opencv(video_path, sample_every_sec=1.0):
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {
            "summary": {
                "frontRatio": 0,
                "leftRatio": 0,
                "rightRatio": 0,
                "noFaceRatio": 1,
                "sampleCount": 0,
                "feedback": "영상을 열 수 없어 시선 분석을 수행하지 못했습니다."
            },
            "issues": []
        }

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    frame_interval = max(1, int(fps * sample_every_sec))

    front_count = 0
    no_face_count = 0
    sample_count = 0
    issues = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_idx % frame_interval != 0:
            frame_idx += 1
            continue

        time_sec = frame_idx / fps
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        sample_count += 1

        if len(faces) > 0:
            front_count += 1
        else:
            no_face_count += 1
            issues.append({
                "type": "gaze_no_face",
                "category": "gaze",
                "label": "얼굴 미검출",
                "start": round(time_sec, 2),
                "end": round(time_sec + sample_every_sec, 2),
                "time": format_time(time_sec),
                "message": "얼굴이 감지되지 않았습니다."
            })

        frame_idx += 1

    cap.release()

    total = sample_count if sample_count > 0 else 1
    front_ratio = front_count / total
    no_face_ratio = no_face_count / total

    if front_ratio >= 0.65:
        feedback = "정면 얼굴 감지 비율이 높은 편입니다."
    elif front_ratio >= 0.4:
        feedback = "정면 얼굴이 일부 감지되지만, 얼굴 미검출 구간이 있습니다."
    else:
        feedback = "정면 얼굴 감지 비율이 낮아 시선 처리 보완이 필요합니다."

    return {
        "summary": {
            "frontRatio": round(front_ratio, 2),
            "leftRatio": 0,
            "rightRatio": 0,
            "noFaceRatio": round(no_face_ratio, 2),
            "sampleCount": sample_count,
            "feedback": feedback
        },
        "issues": issues
    }
