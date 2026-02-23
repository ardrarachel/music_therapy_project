import os
import time
import random
import threading
import socket
import pygame
import speech_recognition as sr
import librosa
import numpy as np

# ----------------- CONSTANTS -----------------
BASE_PATH = os.path.join(os.getcwd(), "audio")

EMOTION_PATHS = {
    "Sad": os.path.join(BASE_PATH, "sad"),
    "Angry": os.path.join(BASE_PATH, "angry"),
    "Neutral": os.path.join(BASE_PATH, "neutral"),
    "Happy": os.path.join(BASE_PATH, "happy"),
    "Surprised": os.path.join(BASE_PATH, "surprised")
}

ISO_FLOW = {
    "Sad": ["Sad", "Neutral", "Happy"],
    "Angry": ["Angry", "Neutral", "Happy"],
    "Neutral": ["Neutral", "Happy"],
    "Happy": ["Happy"],
    "Surprised": ["Surprised", "Happy"]
}

# ----------------- MUSIC PLAYER LOGIC -----------------
# (Maintained for App Compatibility)

def init_player():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def load_songs(folder):
    print(f"🔍 Loading songs from folder: {folder}")

    if not os.path.exists(folder):
        print(f"⚠ Folder missing: {folder}")
        return []
    songs = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".mp3")]
    # print(f"🎵 Found songs: {songs}") 
    return songs

def build_iso_playlist(start_emotion):
    flow = ISO_FLOW.get(start_emotion, ["Neutral"])
    playlist = []

    for emotion in flow:
        folder = EMOTION_PATHS.get(emotion)
        songs = load_songs(folder)
        if songs:
            playlist.append(random.choice(songs))
            
    print("🎶 Playlist:", playlist)
    return playlist

def play_playlist_thread(playlist):
    init_player()
    for song in playlist:
        print(f"▶ Playing: {song}")
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)

def start_music_therapy(emotion):
    print(f"\n🔥 Starting Music Therapy | Mood: {emotion}")
    playlist = build_iso_playlist(emotion)

    if not playlist:
        print("❌ No songs found for therapy")
        return

    threading.Thread(target=play_playlist_thread, args=(playlist,), daemon=True).start()


# ----------------- EXPERT PHYSICS AUDIO LOGIC -----------------

def calculate_intensity(energy, pitch, emotion):
    """
    Normalizes and fuses Energy and Pitch into a 0.0-1.0 Intensity Score.
    """
    # Normalize Energy (Assuming max expected RMS ~0.3 based on typical mic input)
    norm_energy = min(1.0, energy / 0.25)
    
    # Normalize Pitch Variance (Assuming max ZCR variance ~0.15)
    norm_pitch = min(1.0, pitch / 0.15)
    
    # Weighted Formula
    intensity = (norm_energy * 0.7) + (norm_pitch * 0.3)
    
    return round(intensity, 3)

def analyze_voice_input(file_path):
    """
    Analyzes audio using Signal Processing Physics and Heuristic Logic.
    NO Machine Learning Classifiers used.
    """
    result = {
        "text": "No transcription",
        "emotion": "Neutral",
        "energy_score": 0.0,
        "pitch_score": 0.0,
        "intensity": 0.0
    }

    print("\n--- [START AUDIO ANALYSIS] ---")

    # 1. SPEECH RECOGNITION (English Only)
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            print("   [SPEECH] Recording for transcription...")
            # Adjust for ambient noise to help Google hear quiet voices better
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Add a slight amplification to the audio data for the API
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='en-US')
            print(f"   [SPEECH] Recognized: \"{text}\"")
            result['text'] = text
            
    except sr.UnknownValueError:
        print("   [SPEECH] Unintelligible.")
        result['text'] = "(Unintelligible)"
    except Exception as e:
        print(f"   [SPEECH] Error: {e}")

    # 2. PHYSICS SIGNAL PROCESSING
    try:
        # Load Audio (Librosa)
        y, sr_rate = librosa.load(file_path)
        
        # --- A. NOISE GATE (Dynamic) ---
        peak_volume = np.max(np.abs(y))
        # Lowered noise threshold from 0.25 to 0.10 so it doesn't aggressively delete quiet speech
        noise_threshold = 0.10 * peak_volume
        
        # Create a mask where signal > threshold (Keep only loud parts)
        # We process the 'clean' signal for physics extraction
        y_clean = y[np.abs(y) >= noise_threshold]
        
        removed_ratio = 1.0 - (len(y_clean) / len(y))
        print(f"   [PHYSICS] Noise Gate: Removed {removed_ratio*100:.1f}% of audio (Silence/Hiss)")

        if len(y_clean) == 0:
            print("   [PHYSICS] Signal too low. Defaulting to Neutral.")
            return result
        
        # --- B. ENERGY (Loudness) -> RMS ---
        # Calculate RMS of the GATED signal
        rms = librosa.feature.rms(y=y_clean)[0]
        energy = float(np.mean(rms))
        print(f"   [PHYSICS] Energy (RMS): {energy:.4f}")
        
        # --- C. PITCH (Tone/Variance) -> ZCR ---
        # Zero Crossing Rate indicates how "noisy" or "rapid" the signal changes frequency
        # Low ZCR = Monotone/Deep. High ZCR = Bright/Excited/Squeaky.
        zcr = librosa.feature.zero_crossing_rate(y=y_clean)[0]
        zcr_mean = float(np.mean(zcr))
        zcr_var = float(np.var(zcr)) # Variance of the ZCR
        
        # Use Variance as the primary "Pitch Score" for excitement detection
        pitch_score = zcr_var 
        print(f"   [PHYSICS] Pitch (ZCR Var): {pitch_score:.4f}")
        
        result['energy_score'] = round(energy, 4)
        result['pitch_score'] = round(pitch_score, 4)
        
        # 3. HEURISTIC CLASSIFICATION RULES
        # Rules defined by the User
        
        emotion = "Neutral"
        
        # Rule 1: SADNESS
        # Low Energy (< 0.025)
        if energy < 0.025:
             emotion = "Sad"
             print("   [LOGIC] Rule Match: Low Energy -> SAD")
             
        # Rule 2: ANGER (Specific Case: VERY LOUD + STEADY)
        # Raised threshold to 0.18 to prevent "loud talking" from triggering it.
        # Added "Hum Check": If variance is < 0.002, it's likely a fan/noise, NOT anger.
        elif energy > 0.18: 
            if pitch_score < 0.002:
                emotion = "Neutral" # Likely Noise/Hum
                print("   [LOGIC] Rule Match: High Energy + Flat Tone -> NOISE/NEUTRAL (Hum Filter)")
            elif pitch_score < 0.010: # Very Steady, but not flat
                emotion = "Angry"
                print("   [LOGIC] Rule Match: Very High Energy (0.18+) + Steady Tone -> ANGER")
            else:
                emotion = "Excited"
                print("   [LOGIC] Rule Match: Very High Energy + variance -> EXCITED")

        # Rule 3: HAPPY / EXCITED (General high energy case)
        # If energy is medium-high (0.05+) but not "Angry" steady
        elif energy > 0.05:
            # We catch almost everything here to bias towards Positive/Neutral
            if pitch_score > 0.015:
                emotion = "Happy"
                print("   [LOGIC] Rule Match: Med-High Energy + Variance -> HAPPY")
            else:
                emotion = "Neutral" 
                print("   [LOGIC] Rule Match: Med-High Energy + Steady -> NEUTRAL")
                
        # Rule 4: NEUTRAL (Medium energy, lowish variance)
        else:
             emotion = "Neutral"
             
        result['emotion'] = emotion
        
        # 4. INTENSITY SCORE
        result['intensity'] = calculate_intensity(energy, pitch_score, emotion)
        print(f"   [LOGIC] Intensity Score: {result['intensity']}")

    except Exception as e:
        print(f"   [ERROR] Physics Processing Failed: {e}")
        
    return result
