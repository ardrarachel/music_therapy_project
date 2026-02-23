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
from real_emotion import analyze_face # Make sure this is at the top

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
        emotion_text, metrics = analyze_face(image_path)
        
        # 4. Extract just the main emotion word (e.g., "Happy" from "Happy: Corners lifted")
        main_emotion = emotion_text.split(":")[0] 
        
        # 5. Send clean JSON back to JavaScript
        return jsonify({
            'emotion': main_emotion,
            'details': emotion_text,
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

    # Voice emotion teammate will build later
    simulated_voice_emotion = "Neutral"

    current_state['voice_emotion'] = simulated_voice_emotion
    current_state['last_spoken_text'] = "Voice processed"

    # --------- FUSION ENGINE DECIDES FINAL MOOD ----------
    face_val = current_state['face_emotion']
    voice_val = simulated_voice_emotion

    fusion_result = fusion_engine.fuse_emotions(face_val, voice_val)
    current_state['final_mood'] = fusion_result['final_mood']

    print(f"\n🎭 Face: {face_val} | 🎤 Voice: {voice_val} | 🧠 Final Mood: {current_state['final_mood']}")

    # --------- 🎵 YOUR MUSIC THERAPY MODULE RUNS ----------
    start_music_therapy(current_state['final_mood'])

    return jsonify({
        "bot_reply": "Music therapy started.",
        "new_mood": current_state['final_mood'],
        "confidence": fusion_result['confidence'],
        "reasoning": fusion_result['reasoning']
    })


# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(debug=False)
