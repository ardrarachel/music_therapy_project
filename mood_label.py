import librosa
import numpy as np
import speech_recognition as sr
import os
import pygame
import time

def analyze_voice_input(file_path):
    """
    Analyze a voice input file and return detected text, emotion, energy, and pitch scores.
    Only considers 5 emotions: happy, sad, angry, surprised, neutral
    """
    result = {
        "text": "(Voice Only)",
        "emotion": "neutral",
        "energy_score": 0.0,
        "pitch_score": 0.0
    }

    # --- SPEECH TO TEXT ---
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300

    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            try:
                # English first
                text = recognizer.recognize_google(audio_data, language='en-US')
                result['text'] = text
            except sr.UnknownValueError:
                # Try Malayalam
                try:
                    text_ml = recognizer.recognize_google(audio_data, language='ml-IN')
                    result['text'] = text_ml
                except:
                    result['text'] = "(Could not understand)"
            except sr.RequestError:
                print("[ERROR] No internet connection for speech recognition.")
    except Exception as e:
        print(f"[CRITICAL] Speech Recognition failed: {e}")

    # --- PHYSICS & EMOTION LOGIC ---
    try:
        y, sr_rate = librosa.load(file_path)
        max_vol = np.max(np.abs(y))
        y_clean = y[np.abs(y) > (0.25 * max_vol)]
        if len(y_clean) == 0: y_clean = y

        rms = librosa.feature.rms(y=y_clean)
        energy = float(np.mean(rms))

        zcr = librosa.feature.zero_crossing_rate(y=y_clean)
        pitch_var = float(np.mean(zcr))

        result['energy_score'] = energy
        result['pitch_score'] = pitch_var

        # --- MAP ENERGY & PITCH TO 5 EMOTIONS ---
        if energy < 0.015:
            result['emotion'] = "neutral"
        elif energy > 0.08:
            if pitch_var > 0.05:
                result['emotion'] = "surprised"
            else:
                result['emotion'] = "angry"
        elif energy > 0.02:
            if pitch_var > 0.06:
                result['emotion'] = "happy"
            else:
                result['emotion'] = "neutral"
        else:
            if pitch_var < 0.03:
                result['emotion'] = "sad"
            else:
                result['emotion'] = "neutral"

    except Exception as e:
        print(f"[CRITICAL] Physics analysis failed: {e}")

    return result

# --- SONG SELECTION ---
def select_song(emotion):
    """
    Return the path of the song corresponding to the detected emotion.
    """
    song_map = {
        "happy": "audio/malayalam/malayalam_calm.mp3",     # Change to happy song later
        "sad": "audio/malayalam/malayalam_calm.mp3",
        "angry": "audio/malayalam/malayalam_calm.mp3",
        "surprised": "audio/malayalam/malayalam_calm.mp3",
        "neutral": "audio/malayalam/malayalam_calm.mp3"
    }
    return song_map.get(emotion, "audio/malayalam/malayalam_calm.mp3")

# --- PLAY SONG ---
def play_song(song_path):
    if os.path.exists(song_path):
        pygame.mixer.init()
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        print(f"🎵 Playing: {song_path}")
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    else:
        print(f"[ERROR] Song not found: {song_path}")

# --- MAIN TEST ---
if __name__ == "__main__":
    test_song = "audio/malayalam/malayalam_calm.mp3"

    if os.path.exists(test_song):
        print("Malayalam song found ✅")
    else:
        print("Malayalam song NOT found ❌")

    # -------- FAKE EMOTION TEST --------
    # Replace this with analyze_voice_input(file_path)['emotion'] later
    emotion = "Happy"  # Try "Happy", "Sad", "Angry", "Surprised", "Neutral"
    song = select_song(emotion)
    
    print(f"Detected Emotion: {emotion}")
    print(f"🎵 Playing: {song}")

    # -------- PLAY THE SONG --------
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load(song)
    pygame.mixer.music.play()
    
    # Keep running until user presses Enter
    input("Press Enter to stop playback...")
    pygame.mixer.music.stop()
