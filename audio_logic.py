import os
import librosa
import numpy as np
import speech_recognition as sr
import pygame
import sounddevice as sd
from scipy.io.wavfile import write

# --------------------- Voice Recording ---------------------
def record_voice(filename="audio/test_voice.wav", duration=5, fs=44100):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    print(f"Recording your voice for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    print(f"Voice recorded and saved to {filename}")
    return filename

# --------------------- Voice Analysis ---------------------
def analyze_voice_input(file_path):
    result = {
        "text": "(Voice Only)",
        "emotion": "Neutral",
        "energy_score": 0.0,
        "pitch_score": 0.0
    }

    # --- Part A: Speech-to-Text (English + Malayalam) ---
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300

    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='en-US')
                result['text'] = text
                print(f">> USER SAID (English): {text}")
            except sr.UnknownValueError:
                try:
                    text_ml = recognizer.recognize_google(audio_data, language='ml-IN')
                    result['text'] = text_ml
                    print(f">> USER SAID (Malayalam): {text_ml}")
                except:
                    print("   [ERROR] Could not understand Audio in English or Malayalam")
            except sr.RequestError:
                print("   [ERROR] No internet connection for speech recognition")
    except Exception as e:
        print(f"   [CRITICAL] Speech Recognition Crashed: {e}")

    # --- Part B: Physics & Emotion Logic ---
    try:
        y, sr_rate = librosa.load(file_path)

        max_vol = np.max(np.abs(y))
        y_clean = y[np.abs(y) > (0.25 * max_vol)]
        if len(y_clean) == 0:
            y_clean = y

        rms = librosa.feature.rms(y=y_clean)
        energy = float(np.mean(rms))

        zcr = librosa.feature.zero_crossing_rate(y=y_clean)
        pitch_var = float(np.mean(zcr))

        result['energy_score'] = energy
        result['pitch_score'] = pitch_var

        # --- Expert Rules for Emotion ---
        if energy < 0.015:
            result['emotion'] = "Neutral"
        elif energy > 0.08:
            result['emotion'] = "Excited" if pitch_var > 0.05 else "Angry"
        elif energy > 0.02:
            result['emotion'] = "Happy" if pitch_var > 0.06 else "Neutral"
        else:
            result['emotion'] = "Sad" if pitch_var < 0.03 else "Calm"

        print(f"   [PHYSICS] Energy: {energy:.4f}, Pitch: {pitch_var:.4f}")
        print(f"   [EMOTION] Detected Emotion: {result['emotion']}")

    except Exception as e:
        print(f"   [CRITICAL] Physics Engine Failed: {e}")

    return result

# --------------------- Song Selection ---------------------
def select_song(emotion):
    # You can later add more Malayalam songs for different emotions
    if emotion in ["Calm", "Sad"]:
        return "audio/malayalam/malayalam_calm.mp3"
    elif emotion in ["Happy", "Excited"]:
        return "audio/malayalam/malayalam_calm.mp3"
    elif emotion == "Angry":
        return "audio/malayalam/malayalam_calm.mp3"
    else:
        return "audio/malayalam/malayalam_calm.mp3"

# --------------------- Play Song ---------------------
def play_song(song_path):
    if not os.path.exists(song_path):
        print(f"Song not found ❌: {song_path}")
        return

    pygame.mixer.init()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    print(f"Playing song: {song_path}")

    # Wait until song finishes
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# --------------------- MAIN ---------------------
if __name__ == "__main__":
    # --- Step 1: Record voice ---
    import sounddevice as sd
    from scipy.io.wavfile import write

    fs = 44100  # Sampling rate
    duration = 5  # seconds

    print("Recording your voice for 5 seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished

    voice_file = "audio/test_voice.wav"
    write(voice_file, fs, recording)
    print(f"Voice recorded and saved to {voice_file}")

    # --- Step 2: Analyze the recorded voice ---
    result = analyze_voice_input(voice_file)
    print(f"Detected Emotion: {result['emotion']}, Text: {result['text']}")

    # --- Step 3: Select and play the song based on emotion ---
    song_file = select_song(result['emotion'])
    play_song(song_file)
