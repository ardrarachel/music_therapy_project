import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import math
import mediapipe as mp

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
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)




def calculate_distance(point1, point2):
    """
    Helper function to calculate Euclidean distance between two points (x, y).
    """
    return math.hypot(point2[0] - point1[0], point2[1] - point1[1])

def get_emotion(landmarks):
    """
    The main logic function containing the if/else threshold math using Euclidean Geometry.
    """

    # Extract coordinates (using .x and .y directly from landmarks)
    
    # helper to get (x,y) from index
    def get_pt(idx):
        return (landmarks[idx].x, landmarks[idx].y)
    
    # --- Points of Interest ---
    
    # Mouth
    top_lip = get_pt(13)
    bottom_lip = get_pt(14)
    left_corner = get_pt(61)
    right_corner = get_pt(291)
    
    # Eyebrows
    l_brow_inner = get_pt(55)
    r_brow_inner = get_pt(285)
    l_brow_mid = get_pt(105)
    r_brow_mid = get_pt(334)
    
    # --- Geometric Logic ---

    # 1. HAPPY: Lip Corner Angle / Slope
    # Positive value means corners are ABOVE center (Happy) (Y is inverted in image coords usually 0 at top)
    # Center Y - Corner Y > 0 => Corner Y is smaller => Corner is Higher => Smile.
    # FIX: Use ONLY the top lip anchor so talking (jaw dropping) doesn't bias it towards "Happy"
    center_y = top_lip[1]
    corners_y = (left_corner[1] + right_corner[1]) / 2
    smile_val = center_y - corners_y 

    # --- 2. SURPRISE (Mouth Aspect Ratio) ---
    mouth_width = calculate_distance(left_corner, right_corner)
    mouth_height = calculate_distance(top_lip, bottom_lip)
    if mouth_width == 0: mouth_width = 0.001
    mar = mouth_height / mouth_width

    # --- Eyebrow Raise (Shared by Surprise & Angry) ---
    l_eye_top = get_pt(159)
    r_eye_top = get_pt(386)
    l_brow_raise = calculate_distance(l_eye_top, l_brow_mid)
    r_brow_raise = calculate_distance(r_eye_top, r_brow_mid)
    avg_brow_raise = (l_brow_raise + r_brow_raise) / 2

    # --- 3. ANGRY (Glabella) ---
    glabella_dist = calculate_distance(l_brow_inner, r_brow_inner)
    l_eye_outer = get_pt(33)
    r_eye_outer = get_pt(263)
    face_width = calculate_distance(l_eye_outer, r_eye_outer)
    if face_width == 0: face_width = 0.001
    norm_glabella = glabella_dist / face_width

    # --- 4. SAD (Eye Openness) ---
    l_eye_bottom = get_pt(145)
    r_eye_bottom = get_pt(374)
    left_eye_open = calculate_distance(l_eye_top, l_eye_bottom)
    right_eye_open = calculate_distance(r_eye_top, r_eye_bottom)
    avg_eye_open = (left_eye_open + right_eye_open) / 2
    norm_eye_open = avg_eye_open / face_width

    # --- COLLECT METRICS ---
    metrics = {
        "smile": round(smile_val, 4),
        "mar": round(mar, 3),
        "brow_raise": round(avg_brow_raise, 3),
        "glabella": round(norm_glabella, 3),
        "eye_open": round(norm_eye_open, 3)
    }

    # --- LOGIC TRESHOLDS ---
    # 1. ANGRY 
    # Must NOT be smiling (smile_val < 0.0) so a big grin that pinches the face isn't flagged as Angry
    if norm_glabella < 0.32 and smile_val < 0.0: 
         if avg_brow_raise < 0.15:
             return f"Angry: Brows squeezed", metrics

    # 2. HAPPY (Smile > -0.015) - Relaxed negative threshold due to top_lip anchoring
    if smile_val > -0.010:
        return f"Happy: Corners lifted", metrics

    # 3. SURPRISE (MAR > 0.20, Brows > 0.04)
    if mar > 0.20 and avg_brow_raise > 0.04: 
        return f"Surprised: Mouth open", metrics

    # 4. SAD (Smile < -0.035 or Eyes < 0.03)
    if smile_val < -0.035 or norm_eye_open < 0.03:
        return f"Sad: Corners down", metrics

    # 5. NEUTRAL
    return f"Neutral", metrics

def analyze_face(image_path):
    """
    Analyzes the face image at the given path and returns an estimated emotion AND metrics.
    Used by app.py.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return "Neutral", {}

        results = face_mesh_module.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return "Neutral", {} # Return Neutral if no face is found

        # 1. Get the landmarks for the FIRST face detected
        landmarks = results.multi_face_landmarks[0].landmark
        
        # 2. Pass THAT variable to your get_emotion function
        emotion_text, metrics = get_emotion(landmarks) 
        
        return emotion_text, metrics

    except Exception as e:
        print(f"Error in analyze_face: {e}")
        return "Neutral", {}

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
