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

    # 1. Analyze the Voice
    analysis = analyze_voice_input(filepath)
    
    # 2. Analyze the Face (from mid-recording capture)
    if 'face_data' in request.files:
        import real_emotion # Local import
        face_file = request.files['face_data']
        face_path = os.path.join(UPLOAD_FOLDER, "face_response.jpg")
        face_file.save(face_path)
        
        # Analyze this specific frame
        face_emo, _ = real_emotion.analyze_face(face_path)
        print(f"📸 Mid-Recording Face Analysis: {face_emo}")
        
        # Update state so Fusion Engine uses THIS emotion
        current_state['face_emotion'] = face_emo
    
    # 2. Update Voice State
    current_state['voice_emotion'] = analysis['emotion']
    
    # Combined Text Logic
    typed_text = request.form.get('typed_text', '')
    voice_text = analysis['text']
    
    # Normalize: If voice failed, don't include "(Voice Only)" in the fusion text
    if "Voice Only" in voice_text:
        combined_text = typed_text
    else:
        combined_text = f"{typed_text} {voice_text}".strip()
        
    current_state['last_spoken_text'] = combined_text
    
    # 3. FUSION LOGIC (New Tri-Modal System)
    # Get the latest face emotion from the global state (which we just updated)
    
    # Construct Face Sensor Data
    face_data = {
        "emotion": current_state['face_emotion'],
        "confidence": 0.65  # Hardcoded heuristic baseline for now
    }
    
    # Construct Voice Sensor Data
    voice_data = {
        "emotion": analysis['emotion'],
        "energy_score": analysis.get('energy_score', 0.0),
        "pitch_score": analysis.get('pitch_score', 0.0)
    }
    
    # Call the new Fusion Engine with COMBINED text
    fusion_result = fusion_engine.fuse_multimodal_sensors(face_data, voice_data, combined_text)
    
    current_state['final_mood'] = fusion_result['final_mood']
    
    print(f"🗣️ User Input: '{combined_text}' | Fused Mood: {current_state['final_mood']}")

    return jsonify({
        "bot_reply": f"I understood: '{combined_text}'.",
        "new_mood": current_state['final_mood'],
        "confidence": fusion_result['confidence'],
        "reasoning": fusion_result['reasoning']
    })


# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(debug=True,port=5001)

