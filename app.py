from flask import Flask, render_template, request, jsonify
import os

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
@app.route('/detect_face', methods=['POST'])
def detect_face():
    import real_emotion # Local import to avoid circular dependency issues if any
    
    if 'face_image' not in request.files:
        return jsonify({"error": "No face image"}), 400
    
    file = request.files['face_image']
    filepath = os.path.join(UPLOAD_FOLDER, "face_capture.jpg")
    file.save(filepath)

    # Analyze face
    emotion, metrics = real_emotion.analyze_face(filepath)
    
    # Update Global State
    current_state['face_emotion'] = emotion

    return jsonify({
        "status": "success", 
        "emotion": emotion,
        "metrics": metrics
    })

@app.route('/update_face', methods=['POST'])
def update_face():
    data = request.json
    current_state['face_emotion'] = data.get('emotion', 'Neutral')
    return jsonify({"status": "face emotion updated"})


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