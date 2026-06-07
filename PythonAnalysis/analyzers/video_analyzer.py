import cv2
import mediapipe as mp
import math


TIMELINE_STYLE = {
    "good": {
        "severity": "good",
        "color": "#22C55E"
    },
    "warning": {
        "severity": "warning",
        "color": "#F59E0B"
    },
    "bad": {
        "severity": "bad",
        "color": "#EF4444"
    },
    "info": {
        "severity": "info",
        "color": "#3B82F6"
    }
}


def make_timeline_event(time, event_type, severity, message):
    style = TIMELINE_STYLE[severity]

    return {
        "time": round(time, 2),
        "type": event_type,
        "severity": style["severity"],
        "color": style["color"],
        "message": message
    }


def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    timeline = []

    if not cap.isOpened():
        return {
            "available": False,
            "error": "영상 파일을 열 수 없습니다."
        }

    if not hasattr(mp, "solutions"):
        cap.release()
        return {
            "available": False,
            "error": "현재 mediapipe 버전에서 solutions API를 사용할 수 없습니다."
        }

    mp_face = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose

    total_frames = 0
    analyzed_frames = 0

    face_count = 0
    eye_contact_count = 0
    pose_count = 0
    gesture_count = 0
    posture_stable_count = 0

    previous_hand_center = None
    previous_body_center = None

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 30

    frame_interval = 10

    last_eye_event_time = -999
    last_gesture_event_time = -999
    last_posture_event_time = -999
    event_gap = 1.0

    with mp_face.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh, mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            total_frames += 1

            if total_frames % frame_interval != 0:
                continue

            analyzed_frames += 1
            current_time = total_frames / fps

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            face_result = face_mesh.process(rgb)
            pose_result = pose.process(rgb)

            if face_result.multi_face_landmarks:
                face_count += 1

                face_landmarks = face_result.multi_face_landmarks[0]

                if is_looking_forward(face_landmarks):
                    eye_contact_count += 1
                else:
                    if current_time - last_eye_event_time >= event_gap:
                        timeline.append(
                            make_timeline_event(
                                current_time,
                                "eye_contact_low",
                                "warning",
                                "시선 이탈"
                            )
                        )
                        last_eye_event_time = current_time
            else:
                if current_time - last_eye_event_time >= event_gap:
                    timeline.append(
                        make_timeline_event(
                            current_time,
                            "face_not_detected",
                            "bad",
                            "얼굴 인식 안 됨"
                        )
                    )
                    last_eye_event_time = current_time

            if pose_result.pose_landmarks:
                valid_pose = has_valid_pose(pose_result.pose_landmarks)

                if valid_pose:
                    pose_count += 1

                current_hand_center = get_hand_center(pose_result.pose_landmarks)
                current_body_center = get_body_center(pose_result.pose_landmarks)

                if has_gesture(pose_result.pose_landmarks, previous_hand_center):
                    gesture_count += 1

                    if current_time - last_gesture_event_time >= event_gap:
                        timeline.append(
                            make_timeline_event(
                                current_time,
                                "gesture",
                                "good",
                                "제스처 사용"
                            )
                        )
                        last_gesture_event_time = current_time

                if is_posture_stable(pose_result.pose_landmarks, previous_body_center):
                    posture_stable_count += 1
                else:
                    if current_time - last_posture_event_time >= event_gap:
                        timeline.append(
                            make_timeline_event(
                                current_time,
                                "posture_unstable",
                                "warning",
                                "자세 흔들림"
                            )
                        )
                        last_posture_event_time = current_time

                if current_hand_center is not None:
                    previous_hand_center = current_hand_center

                if current_body_center is not None:
                    previous_body_center = current_body_center

    cap.release()

    if analyzed_frames == 0:
        return {
            "available": False,
            "error": "분석 가능한 프레임이 없습니다."
        }

    face_detection_rate = face_count / analyzed_frames
    pose_detection_rate = pose_count / analyzed_frames

    eye_contact_available = face_detection_rate >= 0.5
    gesture_available = pose_detection_rate >= 0.3
    posture_available = pose_detection_rate >= 0.3

    eye_contact_rate = eye_contact_count / face_count if eye_contact_available and face_count > 0 else 0
    gesture_rate = gesture_count / pose_count if gesture_available and pose_count > 0 else 0
    posture_stability_rate = posture_stable_count / pose_count if posture_available and pose_count > 0 else 0

    return {
        "available": True,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "analyzed_frames": analyzed_frames,

        "face_detection_rate": round(face_detection_rate, 3),
        "pose_detection_rate": round(pose_detection_rate, 3),
        "eye_contact_available": eye_contact_available,
        "gesture_available": gesture_available,
        "posture_available": posture_available,
        "eye_contact_rate": round(eye_contact_rate, 3),
        "gesture_rate": round(gesture_rate, 3),
        "posture_stability_rate": round(posture_stability_rate, 3),

        "summary": {
            "face_detection_percent": round(face_detection_rate * 100, 1),
            "pose_detection_percent": round(pose_detection_rate * 100, 1),
            "eye_contact_percent": round(eye_contact_rate * 100, 1),
            "gesture_percent": round(gesture_rate * 100, 1),
            "posture_stability_percent": round(posture_stability_rate * 100, 1)
        },

        "timeline": sorted(timeline, key=lambda x: x["time"])[:150]
    }


def is_looking_forward(face_landmarks):
    landmarks = face_landmarks.landmark

    nose = landmarks[1]
    left_face = landmarks[234]
    right_face = landmarks[454]

    face_center_x = (left_face.x + right_face.x) / 2
    face_width = abs(right_face.x - left_face.x)

    if face_width == 0:
        return False

    offset = abs(nose.x - face_center_x) / face_width

    return offset < 0.12


def has_gesture(pose_landmarks, previous_hand_center=None):
    landmarks = pose_landmarks.landmark

    left_wrist = landmarks[15]
    right_wrist = landmarks[16]
    left_hip = landmarks[23]
    right_hip = landmarks[24]

    if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
        return False

    hip_y = (left_hip.y + right_hip.y) / 2

    left_hand_active = left_wrist.visibility >= 0.5 and left_wrist.y < hip_y
    right_hand_active = right_wrist.visibility >= 0.5 and right_wrist.y < hip_y

    if not left_hand_active and not right_hand_active:
        return False

    current_hand_center = get_hand_center(pose_landmarks)
    movement = calculate_movement(current_hand_center, previous_hand_center)

    return movement >= 0.025


def has_valid_pose(pose_landmarks):
    landmarks = pose_landmarks.landmark

    required_indices = [11, 12, 23, 24]

    return all(landmarks[index].visibility >= 0.5 for index in required_indices)


def get_hand_center(pose_landmarks):
    landmarks = pose_landmarks.landmark
    wrists = []

    for index in [15, 16]:
        wrist = landmarks[index]

        if wrist.visibility >= 0.5:
            wrists.append((wrist.x, wrist.y))

    if not wrists:
        return None

    x = sum(point[0] for point in wrists) / len(wrists)
    y = sum(point[1] for point in wrists) / len(wrists)

    return x, y


def get_body_center(pose_landmarks):
    landmarks = pose_landmarks.landmark
    required_indices = [11, 12, 23, 24]
    points = []

    for index in required_indices:
        landmark = landmarks[index]

        if landmark.visibility < 0.5:
            return None

        points.append((landmark.x, landmark.y))

    x = sum(point[0] for point in points) / len(points)
    y = sum(point[1] for point in points) / len(points)

    return x, y


def calculate_movement(current_point, previous_point):
    if current_point is None or previous_point is None:
        return 0

    return math.sqrt(
        (current_point[0] - previous_point[0]) ** 2
        + (current_point[1] - previous_point[1]) ** 2
    )


def is_posture_stable(pose_landmarks, previous_body_center=None):
    landmarks = pose_landmarks.landmark

    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]

    if left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5:
        return False

    shoulder_tilt = abs(left_shoulder.y - right_shoulder.y)
    body_movement = calculate_movement(get_body_center(pose_landmarks), previous_body_center)

    return shoulder_tilt < 0.05 and body_movement < 0.035
