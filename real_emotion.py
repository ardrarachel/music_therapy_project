import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import math
import mediapipe as mp
import datetime

# Direct access to the internal modules to bypass the "solutions" error
try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
except ImportError:
    # Fallback for newer MediaPipe structures
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
# Initialize using the direct reference
face_mesh_module = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)




baseline_metrics = {
    "smile_ratio": 0.0,
    "mar": 0.0,
    "glabella": 0.0,
    "eye_open": 0.0,
    "frown_ratio": 0.0,
    "mouth_width": 0.0
}
calibration_frames = []
baseline_calibrated = False

def calculate_distance(point1, point2):
    """
    Helper function to calculate Euclidean distance between two points (x, y).
    """
    return math.hypot(point2[0] - point1[0], point2[1] - point1[1])

def get_facial_metrics(landmarks):
    def get_pt(idx):
        return (landmarks[idx].x, landmarks[idx].y)
        
    def calc_dist(idx1, idx2):
        return calculate_distance(get_pt(idx1), get_pt(idx2))

    face_width = calc_dist(33, 263)
    if face_width == 0: face_width = 0.001
    
    lip_v_dist = calc_dist(13, 14)
    if lip_v_dist == 0: lip_v_dist = 0.001
    
    mouth_width = calc_dist(61, 291)
    smile_ratio = mouth_width / lip_v_dist
    
    mar = lip_v_dist / mouth_width if mouth_width > 0 else 0
    
    glabella = calc_dist(55, 285) / face_width
    
    avg_eye_open = ((calc_dist(159, 145) + calc_dist(386, 374)) / 2) / face_width
    
    fh_chin_dist = calc_dist(10, 152)
    corners_chin_dist = (calc_dist(61, 152) + calc_dist(291, 152)) / 2
    frown_ratio = corners_chin_dist / fh_chin_dist if fh_chin_dist > 0 else 0
    
    return {
        "smile_ratio": smile_ratio,
        "mar": mar,
        "glabella": glabella,
        "eye_open": avg_eye_open,
        "frown_ratio": frown_ratio,
        "mouth_width": mouth_width
    }

def calibrate_baseline(image_path):
    global baseline_calibrated, baseline_metrics, calibration_frames
    
    try:
        image = cv2.imread(image_path)
        if image is None: return False
        results = face_mesh_module.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks: return False
        
        metrics = get_facial_metrics(results.multi_face_landmarks[0].landmark)
        calibration_frames.append(metrics)
        
        if len(calibration_frames) >= 3:
            for key in baseline_metrics:
                baseline_metrics[key] = sum(f[key] for f in calibration_frames) / len(calibration_frames)
            baseline_calibrated = True
            print(f"✅ BASELINE CALIBRATED: {baseline_metrics}")
            return True
        return False
    except Exception as e:
        print(f"Calibration error: {e}")
        return False

def get_emotion(landmarks):
    metrics = get_facial_metrics(landmarks)
    
    visual_score = {
        "happy": 0.0,
        "sad": 0.0,
        "surprise": 0.0,
        "angry": 0.0,
        "neutral": 0.0
    }
    
    if not baseline_calibrated:
        visual_score["neutral"] = 1.0
        return visual_score, metrics, "Neutral", 0.5
    
    # Calculate deviations
    dev_smile = metrics["mouth_width"] / (baseline_metrics.get("mouth_width", 1.0) if baseline_metrics.get("mouth_width", 0) > 0 else 1.0)
    dev_frown = metrics["frown_ratio"] / (baseline_metrics["frown_ratio"] if baseline_metrics["frown_ratio"] > 0 else 1.0)
    dev_glabella = metrics["glabella"] / (baseline_metrics["glabella"] if baseline_metrics["glabella"] > 0 else 1.0)
    dev_mar = metrics["mar"] / (baseline_metrics["mar"] if baseline_metrics["mar"] > 0 else 1.0)
    dev_eye_open = metrics["eye_open"] / (baseline_metrics["eye_open"] if baseline_metrics["eye_open"] > 0 else 1.0)
    
    any_deviation = False
    
    # Require a 5% increase in pure width to trigger "Happy" to prevent false positives from talking
    if dev_smile > 1.05:
        visual_score["happy"] = min(1.0, (dev_smile - 1.05) * 15)
        any_deviation = True
        
    if dev_frown < 0.97: # Slightly softer constraint for sadness
        visual_score["sad"] = min(1.0, (0.97 - dev_frown) * 15)
        any_deviation = True
        
    # Surprise must also involve widened eyes to prevent regular talking or sadness from triggering MAR
    if dev_mar > 1.20 and dev_eye_open > 1.03:
        visual_score["surprise"] = min(1.0, (dev_mar - 1.20) * 3)
        any_deviation = True
        
    if dev_glabella < 0.98: # Glabella doesn't squeeze much, make constraint softer
        visual_score["angry"] = min(1.0, (0.98 - dev_glabella) * 15)
        any_deviation = True
        
    if not any_deviation or max(visual_score.values()) < 0.20:
        visual_score["neutral"] = 1.0
        
    best_emotion = max(visual_score, key=visual_score.get)
    confidence = max(0.5, visual_score[best_emotion])
    
    if best_emotion == "neutral":
        confidence = 0.85
        
    return visual_score, metrics, best_emotion.capitalize(), confidence

def analyze_face(image_path):
    default_payload = {
        "visual_score": {"neutral": 1.0},
        "confidence": 0.5,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "main_emotion": "Neutral"
    }
    try:
        image = cv2.imread(image_path)
        if image is None: return default_payload, {}

        results = face_mesh_module.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks: return default_payload, {}

        landmarks = results.multi_face_landmarks[0].landmark
        visual_score, metrics, main_emotion_str, conf = get_emotion(landmarks) 
        
        payload = {
            "visual_score": visual_score,
            "confidence": round(conf, 2),
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "main_emotion": main_emotion_str
        }
        return payload, metrics

    except Exception as e:
        print(f"Error in analyze_face: {e}")
        return default_payload, {}

def detect_emotion_video():
    """
    Opens the Webcam, draws the face mesh, and prints the calculated emotion 
    on the screen. (Standalone Mode)
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    while True:
        success, image = cap.read()
        if not success:
            break

        # Convert the BGR image to RGB.
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh_module.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Draw mesh (optional, simplified drawing points)
                h, w, c = image.shape
                for idx, lm in enumerate(face_landmarks.landmark):
                    # Draw only key points to avoid clutter
                    if idx in [13, 14, 61, 291, 55, 285]: 
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(image, (cx, cy), 2, (0, 255, 0), -1)

                # Get Emotion
                emotion_full = get_emotion(face_landmarks.landmark)
                
                # Display
                cv2.putText(image, emotion_full, (20, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow('Geometric Emotion Detection', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_emotion_video()
