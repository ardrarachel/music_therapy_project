import librosa
import numpy as np
import speech_recognition as sr
import os

def analyze_voice_input(file_path):
    """
    Analyzes spoken response.
    1. Extracts 'Tone' (Emotion) using Signal Processing (Physics).
    2. Transcribes text (Content) using Google API.
    """
    result = {
        "text": "",
        "emotion": "Neutral",
        "energy_score": 0.0,
        "pitch_score": 0.0
    }
    
    try:
        # --- PART A: SPEECH TO TEXT (Google API) ---
        # We use this to know WHAT they said, but rely on Physics for HOW they felt.
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                result['text'] = text
            except sr.UnknownValueError:
                result['text'] = "(Unintelligible)"

        # --- PART B: ACOUSTIC ANALYSIS (Librosa - The White Box Logic) ---
        # Load audio (Floating point time series)
        y, sr_rate = librosa.load(file_path, duration=5.0)

        # 1. Calculate Energy (Root Mean Square)
        rms = librosa.feature.rms(y=y)
        energy = np.mean(rms)
        result['energy_score'] = float(energy)

        # 2. Calculate Pitch Variation (Zero Crossing Rate)
        zcr = librosa.feature.zero_crossing_rate(y=y)
        pitch_var = np.mean(zcr)
        result['pitch_score'] = float(pitch_var)

        # 3. Expert Rules (Thresholding)
        # Note: These values need calibration based on your mic sensitivity
        if energy > 0.05:
            if pitch_var > 0.1:
                result['emotion'] = "Excited/Happy" # Loud + Fast
            else:
                result['emotion'] = "Angry/Stressed" # Loud + Monotone
        elif energy < 0.015:
            result['emotion'] = "Sad/Depressed" # Quiet + Slow
        else:
            result['emotion'] = "Neutral"

        return result

    except Exception as e:
        print(f"Error analyzing voice: {e}")
        return result