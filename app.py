from flask import Flask, render_template, request, jsonify
import os
from audio_logic import analyze_voice_input
import real_emotion
import fusion_engine

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global State
current_state = {
    "face_emotion": "Neutral",
    "voice_emotion": "Neutral",
    "last_spoken_text": "",
    "final_mood": "Neutral"
}

@app.route('/')
def index():
    return render_template('index.html')

# --- ROUTE FOR MEMBER 1 (Camera) ---
# Updated to receive actual image data from frontend loop
@app.route('/detect_face', methods=['POST'])
def detect_face():
    if 'face_image' not in request.files:
        return jsonify({"error": "No face image"}), 400
    
    file = request.files['face_image']
    filepath = os.path.join(UPLOAD_FOLDER, "face_capture.jpg")
    file.save(filepath)

    # Analyze face
    emotion = real_emotion.analyze_face(filepath)
    
    # Update Global State
    current_state['face_emotion'] = emotion

    return jsonify({"status": "success", "emotion": emotion})

@app.route('/update_face', methods=['POST'])
def update_face():
    # Keep old route for backward compatibility if needed, or redirect logic
    data = request.json
    current_state['face_emotion'] = data.get('emotion', 'Neutral')
    return jsonify({"status": "updated"})

# --- ROUTE FOR MEMBER 2 (Your Audio Logic) ---
@app.route('/process_voice_answer', methods=['POST'])
def process_voice_answer():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio"}), 400

    file = request.files['audio_data']
    # Save as WAV (Make sure frontend sends WAV blob)
    filepath = os.path.join(UPLOAD_FOLDER, "response.wav")
    file.save(filepath)

    # 1. Analyze the Voice
    analysis = analyze_voice_input(filepath)
    
    # 2. Update State
    current_state['voice_emotion'] = analysis['emotion']
    current_state['last_spoken_text'] = analysis['text']
    
    # 3. FUSION LOGIC (New Expert System)
    # Get the latest face emotion from the global state
    face_val = current_state['face_emotion']
    voice_val = analysis['emotion']
    
    fusion_result = fusion_engine.fuse_emotions(face_val, voice_val)
    
    current_state['final_mood'] = fusion_result['final_mood']
    
    print(f"🗣️ User Said: '{analysis['text']}' | Fused Mood: {current_state['final_mood']}")

    return jsonify({
        "bot_reply": f"I heard you say '{analysis['text']}'.",
        "new_mood": current_state['final_mood'],
        "confidence": fusion_result['confidence'],
        "reasoning": fusion_result['reasoning']
    })

if __name__ == '__main__':
    app.run(debug=True)