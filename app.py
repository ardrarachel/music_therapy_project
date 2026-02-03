from flask import Flask, render_template, request, jsonify
import os

from audio_logic import start_music_therapy
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

<<<<<<< HEAD
    # 1. Analyze the Voice
    analysis = analyze_voice_input(filepath)
    
    # 2. Update State
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
    # Get the latest face emotion from the global state
    
    # Construct Face Sensor Data
    face_data = {
        "emotion": current_state['face_emotion'],
        "confidence": 0.65  # Hardcoded heuristic baseline for now
    }
    
    # Construct Voice Sensor Data
    voice_data = {
        "emotion": analysis['emotion'],
        "energy_score": analysis['energy_score'],
        "pitch_score": analysis['pitch_score']
    }
    
    # Call the new Fusion Engine with COMBINED text
    fusion_result = fusion_engine.fuse_multimodal_sensors(face_data, voice_data, combined_text)
    
    current_state['final_mood'] = fusion_result['final_mood']
    
    print(f"🗣️ User Input: '{combined_text}' | Fused Mood: {current_state['final_mood']}")

    return jsonify({
        "bot_reply": f"I understood: '{combined_text}'.",
=======
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
>>>>>>> 08d7a3ff9b904035e4c07b88592bfc148bb4d581
        "new_mood": current_state['final_mood'],
        "confidence": fusion_result['confidence'],
        "reasoning": fusion_result['reasoning']
    })


# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(debug=False)

