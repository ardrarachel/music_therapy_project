from flask import Flask, render_template, request, jsonify
import os
from audio_logic import analyze_voice_input
import real_emotion

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
    
    # 3. FUSION LOGIC (Voice Priority)
    # Since the user just answered a question, their Voice is the most relevant signal.
    # We override the camera for this specific moment.
    
    if analysis['emotion'] != "Neutral":
        current_state['final_mood'] = analysis['emotion']
        reason = "Detected vocal tone cues."
    else:
        # If voice is neutral, fall back to what the face shows
        current_state['final_mood'] = current_state['face_emotion']
        reason = "Voice was neutral, relying on face."

    print(f"🗣️ User Said: '{analysis['text']}' | Tone: {analysis['emotion']}")

    return jsonify({
        "bot_reply": f"I heard you say '{analysis['text']}'. You sound {analysis['emotion']}.",
        "new_mood": current_state['final_mood']
    })

if __name__ == '__main__':
    app.run(debug=True)