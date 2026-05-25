import math
import cv2
import mediapipe as mp


def format_time(seconds):
    minute = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minute:02d}:{sec:02d}"


def distance(p1, p2):
    if p1 is None or p2 is None:
        return 0

    return math.sqrt(
        (p1[0] - p2[0]) ** 2
        + (p1[1] - p2[1]) ** 2
    )


def get_hand_positions(pose_landmarks, width, height):
    if pose_landmarks is None:
        return None, None

    landmarks = pose_landmarks.landmark

    left_wrist = landmarks[15]
    right_wrist = landmarks[16]

    if left_wrist.visibility < 0.4:
        left_pos = None
    else:
        left_pos = (left_wrist.x * width, left_wrist.y * height)

    if right_wrist.visibility < 0.4:
        right_pos = None
    else:
        right_pos = (right_wrist.x * width, right_wrist.y * height)

    return left_pos, right_pos


def analyze_gesture(video_path, sample_every_sec=0.5):
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {
            "summary": {
                "gestureLevel": "분석 실패",
                "movementScore": 0,
                "feedback": "영상을 열 수 없어 손동작 분석을 수행하지 못했습니다."
            },
            "issues": []
        }

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    frame_interval = max(1, int(fps * sample_every_sec))

    prev_left = None
    prev_right = None

    movement_values = []
    issues = []

    low_movement_window = []
    current_low_start = None

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

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
            results = pose.process(rgb)

            left_pos, right_pos = get_hand_positions(
                results.pose_landmarks,
                width,
                height
            )

            left_move = distance(prev_left, left_pos)
            right_move = distance(prev_right, right_pos)

            movement = left_move + right_move
            movement_values.append(movement)

            # 움직임 기준값
            # 영상 해상도에 따라 달라지므로 폭 기준으로 정규화
            normalized_movement = movement / width

            if normalized_movement < 0.015:
                if current_low_start is None:
                    current_low_start = time_sec
            else:
                if current_low_start is not None:
                    duration = time_sec - current_low_start

                    if duration >= 3.0:
                        issues.append({
                            "type": "low_gesture",
                            "category": "gesture",
                            "label": "손동작 부족",
                            "start": round(current_low_start, 2),
                            "end": round(time_sec, 2),
                            "duration": round(duration, 2),
                            "time": format_time(current_low_start),
                            "message": f"{duration:.1f}초 동안 손동작이 적었습니다."
                        })

                    current_low_start = None

            prev_left = left_pos
            prev_right = right_pos

            frame_idx += 1

    cap.release()

    if current_low_start is not None:
        end_time = frame_idx / fps
        duration = end_time - current_low_start

        if duration >= 3.0:
            issues.append({
                "type": "low_gesture",
                "category": "gesture",
                "label": "손동작 부족",
                "start": round(current_low_start, 2),
                "end": round(end_time, 2),
                "duration": round(duration, 2),
                "time": format_time(current_low_start),
                "message": f"{duration:.1f}초 동안 손동작이 적었습니다."
            })

    if not movement_values:
        avg_movement = 0
    else:
        avg_movement = sum(movement_values) / len(movement_values)

    movement_score = avg_movement

    if movement_score < 8:
        gesture_level = "적음"
        feedback = "손동작이 적어 발표가 다소 정적으로 보일 수 있습니다."
    elif movement_score < 25:
        gesture_level = "보통"
        feedback = "손동작이 어느 정도 사용되었습니다."
    else:
        gesture_level = "많음"
        feedback = "손동작이 활발한 편입니다. 과도하면 산만해 보일 수 있습니다."

    return {
        "summary": {
            "gestureLevel": gesture_level,
            "movementScore": round(movement_score, 2),
            "lowGestureCount": len(issues),
            "feedback": feedback
        },
        "issues": issues
    }