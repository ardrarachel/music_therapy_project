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
    "lip_drop": 0.0,
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
    # Using vertical lip distance as denominator is unstable during speech/frowns.
    # We will normalize smile width by face width instead.
    smile_ratio = mouth_width / face_width
    
    mar = lip_v_dist / mouth_width if mouth_width > 0 else 0
    
    glabella = calc_dist(55, 285) / face_width
    
    avg_eye_open = ((calc_dist(159, 145) + calc_dist(386, 374)) / 2) / face_width
    
    # Isolate true vertical movement of lip corners relative to the nose tip (4).
    # Face axis from chin (152) to forehead (10)
    axis_dx = landmarks[10].x - landmarks[152].x
    axis_dy = landmarks[10].y - landmarks[152].y
    axis_len = math.hypot(axis_dx, axis_dy) + 0.0001
    v_x, v_y = axis_dx/axis_len, axis_dy/axis_len
    
    def get_vertical_dist(idx_bottom, idx_top):
        dx = landmarks[idx_top].x - landmarks[idx_bottom].x
        dy = landmarks[idx_top].y - landmarks[idx_bottom].y
        return (dx * v_x + dy * v_y)
        
    lip_drop_left = get_vertical_dist(61, 4)
    lip_drop_right = get_vertical_dist(291, 4)
    lip_drop = (lip_drop_left + lip_drop_right) / (2 * face_width)
    
    return {
        "smile_ratio": smile_ratio,
        "mar": mar,
        "glabella": glabella,
        "eye_open": avg_eye_open,
        "lip_drop": lip_drop,
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
    dev_smile_ratio = metrics["smile_ratio"] / (baseline_metrics.get("smile_ratio", 1.0) if baseline_metrics.get("smile_ratio", 0) > 0 else 1.0)
    dev_lip_drop = metrics["lip_drop"] / (baseline_metrics["lip_drop"] if baseline_metrics["lip_drop"] > 0 else 1.0)
    dev_glabella = metrics["glabella"] / (baseline_metrics["glabella"] if baseline_metrics["glabella"] > 0 else 1.0)
    dev_mar = metrics["mar"] / (baseline_metrics["mar"] if baseline_metrics["mar"] > 0 else 1.0)
    dev_eye_open = metrics["eye_open"] / (baseline_metrics["eye_open"] if baseline_metrics["eye_open"] > 0 else 1.0)
    
    print(f"[DEBUG DEV] smile:{dev_smile_ratio:.2f} | lip_drop:{dev_lip_drop:.2f} | glabella:{dev_glabella:.2f} | mar:{dev_mar:.2f} | eye:{dev_eye_open:.2f}")

    any_deviation = False
    
    # 1. HAPPY (Smile):
    # A true smile pulls the lip corners UP towards the nose (lip_drop < 1.0).
    # We trigger happy if the mouth widens AND the corners don't physically drop down like a frown.
    if dev_smile_ratio > 1.05 and dev_lip_drop < 1.05:
        visual_score["happy"] = min(1.0, (dev_smile_ratio - 1.05) * 12.0)
        any_deviation = True
        
    # 2. SAD: Lip corners drop OR pout (mouth narrows) OR wry sadness (squint + slight smile).
    # When sad, your lip corners either pull DOWN visibly (lip_drop >= 1.03) 
    # OR you pout, causing the mouth to narrow (smile_ratio <= 0.98) and the lips to push down very slightly (lip_drop >= 1.00)
    # OR you exhibit wry sadness (squinting hard with a relaxed/slightly widened mouth and relaxed glabella).
    if (dev_lip_drop >= 1.03 and dev_glabella > 0.90) or \
       (dev_smile_ratio <= 0.98 and dev_lip_drop >= 1.00) or \
       (dev_eye_open <= 0.85 and dev_glabella >= 1.00 and 1.0 <= dev_smile_ratio <= 1.05 and dev_lip_drop <= 0.99): 
        sad_score = 0.0
        if dev_lip_drop >= 1.03:
            sad_score = (dev_lip_drop - 1.03) * 15
        elif dev_smile_ratio <= 0.98:
            sad_score = (0.98 - dev_smile_ratio) * 15 + (dev_lip_drop - 0.99) * 10
        elif dev_eye_open <= 0.85:
            sad_score = (0.85 - dev_eye_open) * 15
        visual_score["sad"] = min(1.0, sad_score)
        any_deviation = True
        
    # 3. SURPRISE: Real surprise demands an open mouth AND widened eyes
    if dev_mar > 1.50 and dev_eye_open > 1.10:
        visual_score["surprise"] = min(1.0, (dev_mar - 1.50) * 2)
        any_deviation = True
        
    # 4. ANGRY: Glabella shrink OR extreme lip drop + squint OR tight grimace.
    is_angry = False
    ang_score = 0.0
    
    # Squeezing glabella
    if dev_glabella <= 0.96: 
        is_angry = True
        ang_score += (0.96 - dev_glabella) * 20
        
    # Massive frown combined with anger traits (squint or glabella squeeze)
    if dev_lip_drop >= 1.05 and (dev_eye_open <= 0.88 or dev_glabella <= 0.96): 
        is_angry = True
        if dev_eye_open <= 0.88:
            ang_score += (0.88 - dev_eye_open) * 15
        if dev_glabella <= 0.96:
            ang_score += (0.96 - dev_glabella) * 15
        ang_score += (dev_lip_drop - 1.05) * 15 
        
    # Tight jaw/grimace (narrow mouth) + slight glabella squeeze or slight squint
    if dev_smile_ratio <= 0.98 and (dev_glabella <= 0.99 or dev_eye_open <= 0.92):
        is_angry = True
        if dev_glabella <= 0.99:
            ang_score += (0.99 - dev_glabella) * 15
        if dev_eye_open <= 0.92:
            ang_score += (0.92 - dev_eye_open) * 15
        ang_score += (0.98 - dev_smile_ratio) * 10
        
    # Intense Stare (relaxed mouth, heavy squint, slight glabella squeeze)
    # MUST ensure smile_ratio is not extremely high (preventing false angry when laughing out loud)
    if dev_eye_open <= 0.88 and dev_glabella <= 0.99 and dev_smile_ratio >= 0.98 and dev_smile_ratio < 1.10 and dev_lip_drop <= 1.02:
        is_angry = True
        ang_score += (0.88 - dev_eye_open) * 20 + (0.99 - dev_glabella) * 10
            
    if is_angry:
        visual_score["angry"] = min(1.0, ang_score)
        any_deviation = True
        
    # Conflict Resolution:
    # If the system detects an intense stare or tight jaw (Angry traits), suppress Happy.
    # However, if the smile ratio is HUGE (> 1.10), the squinting is just from laughing hard
    if (dev_eye_open <= 0.85 or is_angry) and dev_smile_ratio < 1.10:
        visual_score["happy"] = 0.0
        
    # If the system detects a genuine lip drop (frown) or narrowing pout, suppress Happy.
    if dev_lip_drop >= 1.03 or dev_smile_ratio <= 0.98:
        visual_score["happy"] = 0.0
        
    # If Angry traits strongly compete with Sad, let Angry dominate
    if visual_score["angry"] >= 0.5 and visual_score["angry"] >= visual_score["sad"]:
        visual_score["sad"] *= 0.5
        
    # Strong glabella squeeze is definitively angry/concentrating, not purely sad
    if dev_glabella <= 0.96 and visual_score["angry"] > 0.5:
        visual_score["sad"] *= 0.2
        
    if visual_score["sad"] > 0.1 or visual_score["angry"] > 0.1:
        if visual_score["happy"] < 0.5: # Only kill surprise/happy if it's not a dominant smile
            visual_score["surprise"] = 0.0
    if not any_deviation:
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
