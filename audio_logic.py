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
        # We use this to know WHAT they said.
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                result['text'] = text
                print(f">> USER SAID: \"{text}\"") 
            except sr.UnknownValueError:
                result['text'] = "(Unintelligible)"
                print(">> USER SAID: (Unintelligible / Background Noise)")
            except sr.RequestError:
                 result['text'] = "(API Unavailable)"
                 print(">> USER SAID: (Google API Error)")

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

        # 3. Expert Rules (Thresholding - The "Expert System")
        # Logic: We classify based on Physical properties of sound waves.
        
        # DEBUG: Print the Physics values to help tuning
        print(f"   [DEBUG] Energy (Vol): {energy:.4f} | Pitch Var (Tone): {pitch_var:.4f}")

        # TIER 1: HIGH ENERGY (Loud)
        if energy > 0.12:
            if pitch_var > 0.06:
                result['emotion'] = "Surprise" # Very Loud + Variable (Shock/Excitement)
            else:
                result['emotion'] = "Anger"    # Very Loud + Monotone (Shouting)

        # TIER 2: MEDIUM ENERGY (Normal/Conversational)
        elif energy > 0.04:
            # Differentiate based on Tone Variation
            if pitch_var > 0.045:
                # "Subtle Happiness" or "Happy"
                # Moderate volume but valid tonal ups and downs
                result['emotion'] = "Happy" 
            else:
                # Moderate volume but flat tone -> Neutral
                result['emotion'] = "Neutral"

        # TIER 3: LOW ENERGY (Quiet)
        else: # energy < 0.04
            # Very quiet usually implies sadness or withdrawal
            result['emotion'] = "Sadness"   

        return result

    except Exception as e:
        print(f"Error analyzing voice: {e}")
        return result