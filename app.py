import os
# Suppress the massive MediaPipe/TensorFlow C++ logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['GLOG_minloglevel'] = '2'

import cv2
import mediapipe as mp

from flask import Flask, render_template, request, jsonify

from audio_logic import start_music_therapy, analyze_voice_input
import fusion_engine   # teammate's module

app = Flask(__name__)

# Folder to temporarily store audio & images
UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Shared System State
current_state = {
    "face_emotion": "Neutral",
    "voice_emotion": "Neutral",
    "last_spoken_text": "",
    "final_mood": "Neutral"
}

# ---------------- HOME PAGE ----------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------- FACE EMOTION (Teammate 1) ----------------
# Restoring the MISSING /detect_face route
from real_emotion import analyze_face, calibrate_baseline # Make sure this is at the top

@app.route('/calibrate', methods=['POST'])
def calibrate():
    if 'face_image' not in request.files:
        return jsonify({'status': 'error'}), 400
    file = request.files['face_image']
    image_path = "temp_calib.jpg"
    file.save(image_path)
    calibrated = calibrate_baseline(image_path)
    return jsonify({'calibrated': calibrated})

import traceback # Add this at the top of app.py
@app.route('/detect_face', methods=['POST'])
def detect_face():
    print("📸 FRONTEND SENT AN IMAGE! Processing...")
    try:
        # 1. Look for FILES, not JSON
        if 'face_image' not in request.files:
            return jsonify({'error': 'No image provided in form data'}), 400
        
        file = request.files['face_image']
        
        # 2. Save the blob as a temporary image file
        image_path = "temp_face.jpg"
        file.save(image_path)

        # 3. Call your MediaPipe function
        emotion_payload, metrics = analyze_face(image_path)
        
        # 4. Extract just the main emotion word
        main_emotion = emotion_payload.get('main_emotion', 'Neutral')
        
        # --- NEW CODE: Update Global State so Fusion Engine sees it ---
        current_state['face_emotion'] = emotion_payload # Store the whole dict
        print(f"   [FACE CAPTURE] State updated to: {main_emotion}")
        
        # 5. Send clean JSON back to JavaScript
        return jsonify({
            'emotion': main_emotion,
            'details': emotion_payload,
            'metrics': metrics
        })

    except Exception as e:
        print("--- CRASH IN /detect_face ---")
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500


# ---------------- VOICE + MUSIC THERAPY (YOUR PART) ----------------
@app.route('/process_voice_answer', methods=['POST'])
def process_voice_answer():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio"}), 400

    file = request.files['audio_data']
    
    filepath = os.path.join(UPLOAD_FOLDER, "response.wav")
    file.save(filepath)

    # 1. Voice Analysis (Using the physics logic)
    voice_result = analyze_voice_input(filepath)
    voice_val = voice_result['emotion']
    
    # Check if user typed anything manually in the UI
    typed_text = request.form.get('typed_text', '').strip()
    if typed_text:
        user_text = typed_text
        print(f"\n⌨️ [USER TYPED]: {user_text}")
    else:
        user_text = voice_result['text']
        print(f"\n🗣️ [USER SAID]: {user_text}")

    current_state['voice_emotion'] = voice_val
    current_state['last_spoken_text'] = user_text

    # --------- FUSION ENGINE DECIDES FINAL MOOD ----------
    # Grab the recently detected face.
    face_payload = current_state['face_emotion']
    if isinstance(face_payload, dict):
        face_data = face_payload # Passes visual_score, confidence, etc.
        face_val = face_payload.get('main_emotion', 'Neutral')
    else:
        face_data = {'emotion': face_payload, 'confidence': 0.5}
        face_val = face_payload
    
    # Reset face emotion back to Neutral after consuming it, preventing permanent stuck states
    current_state['face_emotion'] = "Neutral"

    # Use the multimodal fusion engine (It will recalculate VADER using user_text automatically)
    fusion_result = fusion_engine.fuse_multimodal_sensors(face_data, voice_result, user_text)
    current_state['final_mood'] = fusion_result['final_mood']

    print(f"\n🎭 Face: {face_val} | 🎤 Voice: {voice_val} | 🧠 Final Mood: {current_state['final_mood']}")

    # --------- 🎵 YOUR MUSIC THERAPY MODULE RUNS ----------
    start_music_therapy(current_state['final_mood'])

    return jsonify({
        "bot_reply": "Music therapy started.",
        "new_mood": current_state['final_mood'],
        "confidence": fusion_result['confidence'],
        "reasoning": fusion_result['reasoning'],
        "user_said": user_text
    })

# (Removed standalone /process_text endpoint per request, everything fuses via Voice trigger now)

# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(port=5001, debug=False)
