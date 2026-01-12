import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
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
    # MediaPipe Y: 0 at top, 1 at bottom. So Smaller Y = Higher up.
    # Center Y - Corner Y > 0 => Corner Y is smaller => Corner is Higher => Smile.
    
    center_y = (top_lip[1] + bottom_lip[1]) / 2
    corners_y = (left_corner[1] + right_corner[1]) / 2
    
    smile_val = center_y - corners_y 
    
    # Threshold for Happy
    if smile_val > 0.015:  # Slightly more sensitive
        return f"Happy: Corners lifted ({smile_val:.3f})"

    # 2. SURPRISE: Mouth Aspect Ratio (MAR) + Eyebrow Raise
    
    mouth_width = calculate_distance(left_corner, right_corner)
    mouth_height = calculate_distance(top_lip, bottom_lip)
    
    if mouth_width == 0: mouth_width = 0.001
    mar = mouth_height / mouth_width
    
    # Eyebrow Raise check relative to eyes
    l_eye_top = get_pt(159)
    r_eye_top = get_pt(386)
    
    l_brow_raise = calculate_distance(l_eye_top, l_brow_mid)
    r_brow_raise = calculate_distance(r_eye_top, r_brow_mid)
    avg_brow_raise = (l_brow_raise + r_brow_raise) / 2

    # Lowered MAR threshold from 0.5 to 0.3 for "subtle" surprise
    # Lowered brow raise slightly
    if mar > 0.25 and avg_brow_raise > 0.04: 
        return f"Surprised: Mouth open ({mar:.2f})"

    # 3. ANGRY: Glabella Distance (Inter-Brow)
    
    glabella_dist = calculate_distance(l_brow_inner, r_brow_inner)
    
    l_eye_outer = get_pt(33)
    r_eye_outer = get_pt(263)
    face_width = calculate_distance(l_eye_outer, r_eye_outer)
    if face_width == 0: face_width = 0.001
    
    norm_glabella = glabella_dist / face_width
    
    # Relaxed thresholds for "Subtle" Anger
    # User Baseline Glabella: ~0.29
    # New Target: < 0.285 (Very sensitive, almost neutral)
    # Increased avg_brow_raise limit to 0.1 to allow for natural brow position
    if norm_glabella < 0.285: 
         if avg_brow_raise < 0.1: # Brows low/normal
             return f"Angry: Brows squeezed ({norm_glabella:.3f})"

    # 4. SAD: Micro-Frown
    # Corners lower than center. (smile_val is negative).
    # Made more sensitive (closer to 0).
    
    if smile_val < -0.005: # Very subtle frown
        return f"Sad: Corners down ({smile_val:.3f})"

    # 5. NEUTRAL - Return debug info to help user trigger emotions
    return f"Neutral (Glab:{norm_glabella:.2f}, Brow:{avg_brow_raise:.2f}, Smile:{smile_val:.3f})"

def analyze_face(image_path):
    """
    Analyzes the face image at the given path and returns an estimated emotion.
    Used by app.py.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return "Neutral"

        # Convert the BGR image to RGB before processing.
        results = face_mesh_module.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return "No Face Detected"

        landmarks = results.multi_face_landmarks[0].landmark
        
        emotion_text = get_emotion(landmarks)
        # Return full text with debug info for now
        return emotion_text

    except Exception as e:
        print(f"Error in analyze_face: {e}")
        return "Neutral"

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
