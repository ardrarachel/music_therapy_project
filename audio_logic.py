import os
<<<<<<< HEAD
import socket
=======
import random
import pygame
import time
import threading
>>>>>>> 08d7a3ff9b904035e4c07b88592bfc148bb4d581

import os
BASE_PATH = os.path.join(os.getcwd(), "audio", "malayalam")

<<<<<<< HEAD
EMOTION_PATHS = {
    "Sad": os.path.join(BASE_PATH, "sad"),
    "Angry": os.path.join(BASE_PATH, "angry"),
    "Neutral": os.path.join(BASE_PATH, "neutral"),
    "Happy": os.path.join(BASE_PATH, "happy"),
    "Surprised": os.path.join(BASE_PATH, "surprised")
}
=======
# --------------------- Voice Analysis ---------------------
def analyze_voice_input(file_path):
    result = {
        "text": "No transcription",
        "emotion": "Neutral",
        "energy_score": 0.0,
        "pitch_score": 0.0
    }
<<<<<<< HEAD
    
    # --- PART A: SPEECH TO TEXT (Dual Language Support) ---
    recognizer = sr.Recognizer()
    # recognizer.energy_threshold = 300  <-- REMOVED: Let it be dynamic
    recognizer.dynamic_energy_threshold = True 
    recognizer.dynamic_energy_adjustment_damping = 0.15 
    
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            print("   [Log] Connecting to Google API...")
            
            # Set a timeout for the API call to prevent hanging
            socket.setdefaulttimeout(3.0)
            
            try:
                # 1. Try English
                text = recognizer.recognize_google(audio_data, language='en-US')
                print(f">> USER SAID: \"{text}\"")
=======
>>>>>>> main

ISO_FLOW = {
    "Sad": ["Sad", "Neutral", "Happy"],
    "Angry": ["Angry", "Neutral", "Happy"],
    "Neutral": ["Neutral", "Happy"],
    "Happy": ["Happy"],
    "Surprised": ["Surprised", "Happy"]
}

<<<<<<< HEAD
=======
    text = ""

    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='en-US')
>>>>>>> 08d7a3ff9b904035e4c07b88592bfc148bb4d581
                result['text'] = text
                print(f">> USER SAID (English): {text}")
            except sr.UnknownValueError:
<<<<<<< HEAD
                print("   [ERROR] Could not understand Audio.")
                    
            except (sr.RequestError, socket.timeout) as e:
                 print(f"   [ERROR] Connection/API Issue: {e}")
                 result['text'] = "(Voice Only - Offline)"

            finally:
                # CRITICAL: Reset timeout to default (None) so we don't affect other parts of the app
                socket.setdefaulttimeout(None)

    except Exception as e:
        print(f"   [CRITICAL] Speech Recognition Crashed: {e}")
        socket.setdefaulttimeout(None) # Safety reset
=======
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
>>>>>>> main

def init_player():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def load_songs(folder):
    print(f"🔍 Loading songs from folder: {folder}")
    if not os.path.exists(folder):
        print(f"⚠ Folder missing: {folder}")
        return []
    songs = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".mp3")]
    print(f"🎵 Found songs: {songs}")
    return songs
>>>>>>> 08d7a3ff9b904035e4c07b88592bfc148bb4d581



def build_iso_playlist(start_emotion):
    flow = ISO_FLOW.get(start_emotion, ["Neutral"])
    playlist = []

    for emotion in flow:
        songs = load_songs(EMOTION_PATHS.get(emotion, ""))
        if songs:
            playlist.append(random.choice(songs))

<<<<<<< HEAD
        # --- EXPERT RULES ---
        
        # Rule 1: Silence
        if energy < 0.02: 
            result['emotion'] = "Neutral" 
            print("   [LOGIC] Ignored as Background Noise")

        # Rule 2: High Energy (Loud)
        elif energy > 0.25: # Raised significantly to 0.25
            if pitch_var > 0.05: result['emotion'] = "Excited"
            else: result['emotion'] = "Anger"

        # Rule 3: Normal Energy (Talking)
        elif energy > 0.10: 
            if pitch_var > 0.11: result['emotion'] = "Happy" # Very strict pitch requirement
            else: result['emotion'] = "Neutral"
=======
    print("🎶 Playlist:", playlist)
    return playlist


def play_playlist_thread(playlist):
    init_player()
>>>>>>> 08d7a3ff9b904035e4c07b88592bfc148bb4d581

    for song in playlist:
        print(f"▶ Playing: {song}")
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()

<<<<<<< HEAD
        while pygame.mixer.music.get_busy():
            time.sleep(1)


def start_music_therapy(emotion):
    print(f"\n🔥 Starting Music Therapy | Mood: {emotion}")

    playlist = build_iso_playlist(emotion)

    if not playlist:
        print("❌ No songs found")
        return

    # ✅ RUN MUSIC IN BACKGROUND
    threading.Thread(target=play_playlist_thread, args=(playlist,), daemon=True).start()
=======
# --------------------- Play Song ---------------------
def play_song(song_path):
    if not os.path.exists(song_path):
        print(f"Song not found ❌: {song_path}")
        try:
            text = recognizer.recognize_google(audio_data, language='en-US')
            result['text'] = text
            print(f">> USER SAID (English): {text}")
        except sr.UnknownValueError:
            try:
                text_ml = recognizer.recognize_google(audio_data, language='ml-IN')
                text = text_ml
                result['text'] = text_ml
                print(f">> USER SAID (Malayalam): {text_ml}")
            except Exception:
                text = ""
                print("   [ERROR] Could not understand Audio in English or Malayalam")
            except sr.RequestError:
                text = ""
                print("   [ERROR] No internet connection for speech recognition")
        except Exception as e:
            text = ""
            print(f"   [CRITICAL] Speech Recognition Crashed: {e}")

    # Ensure a readable transcription value
    if text:
        result['text'] = text
    else:
        result['text'] = "No transcription"

    # Always print a clear transcript line for downstream visibility
    print(f"   [TRANSCRIPT] {result['text']}")

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
>>>>>>> main
