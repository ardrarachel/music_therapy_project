import librosa
import numpy as np
import speech_recognition as sr
import os

def analyze_voice_input(file_path):
    result = {
        "text": "(Voice Only)", 
        "emotion": "Neutral", 
        "energy_score": 0.0, 
        "pitch_score": 0.0
    }
    
    # --- PART A: SPEECH TO TEXT (Dual Language Support) ---
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300 
    
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            print("   [Log] Connecting to Google API...")
            
            try:
                # 1. Try English First
                text = recognizer.recognize_google(audio_data, language='en-US')
                print(f">> USER SAID (English): \"{text}\"")
                result['text'] = text
                
            except sr.UnknownValueError:
                # 2. If English fails, Try Malayalam
                print("   [Log] English failed, trying Malayalam...")
                try:
                    text_ml = recognizer.recognize_google(audio_data, language='ml-IN')
                    print(f">> USER SAID (Malayalam): \"{text_ml}\"")
                    result['text'] = text_ml
                except:
                    print("   [ERROR] Could not understand Audio in Eng or Mal.")
                    
            except sr.RequestError:
                 print("   [ERROR] No Internet Connection.")

    except Exception as e:
        print(f"   [CRITICAL] Speech Recognition Crashed: {e}")


    # --- PART B: PHYSICS & EMOTION LOGIC ---
    try:
        # FIX: Load the file WITHOUT duration limit (reads the whole sentence)
        y, sr_rate = librosa.load(file_path)

        # 1. AGGRESSIVE NOISE GATE (Removes Hiss/Robotic Static)
        max_vol = np.max(np.abs(y))
        y_clean = y[np.abs(y) > (0.25 * max_vol)] # Cut out quiet static
        if len(y_clean) == 0: y_clean = y

        # 2. Physics Calculation
        rms = librosa.feature.rms(y=y_clean)
        energy = float(np.mean(rms))
        
        zcr = librosa.feature.zero_crossing_rate(y=y_clean)
        pitch_var = float(np.mean(zcr))
        
        result['energy_score'] = energy
        result['pitch_score'] = pitch_var
        
        print(f"   [PHYSICS] Energy: {energy:.4f} | Pitch: {pitch_var:.4f}")

        # --- EXPERT RULES ---
        
        # Rule 1: Silence
        if energy < 0.015: 
            result['emotion'] = "Neutral" 
            print("   [LOGIC] Ignored as Background Noise")

        # Rule 2: High Energy (Loud)
        elif energy > 0.08:
            if pitch_var > 0.05: result['emotion'] = "Excited"
            else: result['emotion'] = "Anger"

        # Rule 3: Normal Energy (Talking)
        elif energy > 0.02: 
            if pitch_var > 0.06: result['emotion'] = "Happy"
            else: result['emotion'] = "Neutral"

        # Rule 4: Low Energy (Quiet)
        else:
            if pitch_var < 0.03: result['emotion'] = "Sadness"
            else: result['emotion'] = "Calm"

    except Exception as e:
        print(f"   [CRITICAL] Physics Engine Failed: {e}")

    return result