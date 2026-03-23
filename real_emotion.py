import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import numpy as np
import datetime
import time

# Try to import keras with fallback
try:
    from tensorflow.keras.models import load_model
except:
    from keras.models import load_model

# Define possible model paths (try multiple options)
MODEL_PATHS = [
    "models/emotion_cnn_model.hdf5",
    "models/emotion_cnn_model.h5",
    "emotion_cnn_model.hdf5",
    "emotion_cnn_model.h5",
    "emotion_cnn_model.keras",
    "models/emotion_cnn_model.keras"
]

# Find and load the model
model = None
MODEL_PATH = None

for path in MODEL_PATHS:
    if os.path.exists(path):
        MODEL_PATH = path
        print(f"✅ Found model at: {MODEL_PATH}")
        try:
            # Try loading with compile=False to avoid compatibility issues
            model = load_model(MODEL_PATH, compile=False)
            print("✅ Model loaded successfully!")
            break
        except Exception as e:
            print(f"⚠️ Failed to load model from {path}: {e}")
            continue

if model is None:
    print("❌ ERROR: Could not load emotion model from any location.")
    print("Please ensure the model file exists in one of these locations:")
    for path in MODEL_PATHS:
        print(f"   - {path}")
    print("\nIf you don't have the model, you'll need to train it first.")
    # Don't exit, but set a flag
    MODEL_LOADED = False
else:
    MODEL_LOADED = True

# Emotion labels used in FER2013
emotion_labels = [
    "Angry",
    "Disgust",
    "Fear",
    "Happy",
    "Sad",
    "Surprise",
    "Neutral"
]

# Load OpenCV face detector with fallback
face_cascade = None
cascade_paths = [
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
    "haarcascade_frontalface_default.xml"
]

for path in cascade_paths:
    if os.path.exists(path):
        face_cascade = cv2.CascadeClassifier(path)
        print(f"✅ Loaded face detector from: {path}")
        break

if face_cascade is None:
    print("❌ ERROR: Could not load face cascade classifier.")
    FACE_DETECTOR_LOADED = False
else:
    FACE_DETECTOR_LOADED = True

# Baseline calibration variables
baseline_emotion = "Neutral"
baseline_confidence = 0.5
baseline_timestamp = None


def preprocess_face(face_img):
    """
    Resize and normalize face image for CNN input
    """
    try:
        face = cv2.resize(face_img, (48, 48))
        face = face.astype("float32") / 255.0
        
        # Add batch and channel dimensions
        face = np.reshape(face, (1, 48, 48, 1))
        return face
    except Exception as e:
        print(f"Error preprocessing face: {e}")
        return None


def calibrate_baseline(image_path=None, duration_seconds=3):
    """
    Calibrate baseline emotion from a neutral face.
    If image_path is provided, analyze that image.
    Otherwise, use webcam to capture a neutral face.
    """
    global baseline_emotion, baseline_confidence, baseline_timestamp
    
    print("🔧 Starting baseline calibration...")
    
    if not MODEL_LOADED or not FACE_DETECTOR_LOADED:
        print("⚠️ Model or face detector not loaded. Using default baseline.")
        return {
            "baseline_emotion": baseline_emotion,
            "baseline_confidence": baseline_confidence,
            "baseline_timestamp": baseline_timestamp
        }
    
    try:
        if image_path and os.path.exists(image_path):
            # Analyze from image
            result, _ = analyze_face(image_path)
            if result:
                baseline_emotion = result.get("main_emotion", "Neutral")
                baseline_confidence = result.get("confidence", 0.5)
                baseline_timestamp = result.get("timestamp", datetime.datetime.now().strftime("%H:%M:%S"))
                print(f"✅ Baseline calibrated from image: {baseline_emotion} ({baseline_confidence})")
        else:
            # Use webcam for calibration
            print("📸 Opening webcam for baseline calibration...")
            print("Please look neutral for", duration_seconds, "seconds")
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Cannot open camera for calibration")
                return {
                    "baseline_emotion": baseline_emotion,
                    "baseline_confidence": baseline_confidence,
                    "baseline_timestamp": baseline_timestamp
                }
            
            start_time = time.time()
            frames_processed = 0
            emotion_counts = {}
            
            while time.time() - start_time < duration_seconds:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    face = gray[y:y+h, x:x+w]
                    face_input = preprocess_face(face)
                    
                    if face_input is None:
                        continue
                    
                    prediction = model.predict(face_input, verbose=0)
                    emotion_index = int(np.argmax(prediction))
                    emotion = emotion_labels[emotion_index]
                    
                    # Count emotions
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    frames_processed += 1
                    
                    # Display calibration message
                    cv2.putText(frame, "Calibrating... Please stay neutral", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Time left: {int(duration_seconds - (time.time() - start_time))}s",
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow("Baseline Calibration", frame)
                    
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                
                cv2.imshow("Baseline Calibration", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            # Determine baseline emotion (most frequent)
            if emotion_counts:
                baseline_emotion = max(emotion_counts, key=emotion_counts.get)
                baseline_confidence = emotion_counts[baseline_emotion] / frames_processed if frames_processed > 0 else 0.5
                baseline_timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"✅ Baseline calibrated: {baseline_emotion} (confidence: {baseline_confidence:.2f})")
                print(f"   Processed {frames_processed} frames")
            else:
                print("⚠️ No faces detected during calibration. Using default baseline.")
        
        return {
            "baseline_emotion": baseline_emotion,
            "baseline_confidence": baseline_confidence,
            "baseline_timestamp": baseline_timestamp
        }
        
    except Exception as e:
        print(f"Error during calibration: {e}")
        import traceback
        traceback.print_exc()
        return {
            "baseline_emotion": baseline_emotion,
            "baseline_confidence": baseline_confidence,
            "baseline_timestamp": baseline_timestamp
        }


def analyze_face(image_path):
    """
    Analyze emotion from image file.
    Returns payload compatible with fusion_engine.
    """

    default_payload = {
        "visual_score": {"neutral": 1.0},
        "confidence": 0.5,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "main_emotion": "Neutral"
    }

    if not MODEL_LOADED:
        print("⚠️ Model not loaded. Returning default payload.")
        return default_payload, {}

    try:
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            return default_payload, {}

        image = cv2.imread(image_path)

        if image is None:
            print(f"⚠️ Could not read image: {image_path}")
            return default_payload, {}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) == 0:
            print("⚠️ No faces detected in image")
            return default_payload, {}

        # Process the first face found
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_input = preprocess_face(face_img)
            
            if face_input is None:
                continue

            # Make prediction
            prediction = model.predict(face_input, verbose=0)
            emotion_index = int(np.argmax(prediction))
            confidence = float(np.max(prediction))

            emotion = emotion_labels[emotion_index]

            # Adjust confidence based on baseline if available
            adjusted_confidence = confidence
            if baseline_emotion and baseline_emotion != "Neutral":
                # If baseline is not neutral, adjust confidence
                if emotion == baseline_emotion:
                    adjusted_confidence = max(0.3, confidence - 0.2)
                else:
                    adjusted_confidence = min(0.9, confidence + 0.1)

            payload = {
                "visual_score": {emotion.lower(): adjusted_confidence},
                "confidence": round(adjusted_confidence, 2),
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "main_emotion": emotion,
                "raw_confidence": round(confidence, 2),  # Keep raw confidence for debugging
                "baseline_used": baseline_emotion if baseline_emotion else None
            }

            return payload, {}

        return default_payload, {}

    except Exception as e:
        print(f"Error in analyze_face: {e}")
        import traceback
        traceback.print_exc()
        return default_payload, {}


def detect_emotion_video():
    """
    Standalone webcam testing mode with improved error handling
    """

    if not MODEL_LOADED or not FACE_DETECTOR_LOADED:
        print("❌ Cannot start video detection. Model or face detector not loaded.")
        return

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Cannot open camera. Please check if camera is connected.")
        return

    print("✅ Camera opened successfully. Press 'ESC' to exit.")
    print("Press 'c' to recalibrate baseline")
    
    # For performance, process every few frames
    frame_count = 0
    process_every_n_frames = 2

    while True:
        ret, frame = cap.read()

        if not ret:
            print("⚠️ Failed to grab frame")
            break

        frame_count += 1
        
        # Only process every nth frame for better performance
        if frame_count % process_every_n_frames != 0:
            cv2.imshow("CNN Emotion Detection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('c'):  # Recalibrate
                calibrate_baseline(duration_seconds=3)
            continue

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,  # Slightly faster detection
            minNeighbors=5,
            minSize=(50, 50)  # Minimum face size
        )

        for (x, y, w, h) in faces:
            # Extract face region
            face = gray[y:y+h, x:x+w]
            
            # Preprocess and predict
            face_input = preprocess_face(face)
            
            if face_input is None:
                continue
                
            try:
                prediction = model.predict(face_input, verbose=0)
                emotion_index = int(np.argmax(prediction))
                confidence = float(np.max(prediction))
                emotion = emotion_labels[emotion_index]
                
                # Adjust for baseline
                adjusted_confidence = confidence
                if baseline_emotion and baseline_emotion != "Neutral":
                    if emotion == baseline_emotion:
                        adjusted_confidence = max(0.3, confidence - 0.2)
                
                # Display results
                label = f"{emotion} ({adjusted_confidence:.2f})"
                
                # Show baseline info
                if baseline_emotion:
                    cv2.putText(frame, f"Baseline: {baseline_emotion}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Color based on confidence
                color = (0, int(255 * adjusted_confidence), int(255 * (1 - adjusted_confidence)))
                
                # Draw rectangle and label
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )
                
                # Add confidence bar
                bar_width = int(w * adjusted_confidence)
                cv2.rectangle(frame, (x, y+h+5), (x+bar_width, y+h+15), color, -1)
                
            except Exception as e:
                print(f"Prediction error: {e}")
                continue

        # Show frame
        cv2.imshow("CNN Emotion Detection", frame)

        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('c'):  # Recalibrate
            calibrate_baseline(duration_seconds=3)

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Camera released")


if __name__ == "__main__":
    # You can choose to test with webcam or analyze a single image
    print("🎭 CNN Emotion Detection System")
    print("================================")
    print("1. Start webcam emotion detection")
    print("2. Analyze a single image")
    print("3. Calibrate baseline only")
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        detect_emotion_video()
    elif choice == "2":
        image_path = input("Enter image path: ").strip()
        result, _ = analyze_face(image_path)
        print(f"\n✅ Analysis Result:")
        print(f"   Main Emotion: {result['main_emotion']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Visual Score: {result['visual_score']}")
        print(f"   Timestamp: {result['timestamp']}")
    elif choice == "3":
        calibrate_baseline(duration_seconds=5)
    else:
        print("Invalid choice. Starting webcam detection...")
        detect_emotion_video()