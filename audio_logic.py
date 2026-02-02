import os
import random
import pygame
import time
import threading

import os
BASE_PATH = os.path.join(os.getcwd(), "audio", "malayalam")

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



def build_iso_playlist(start_emotion):
    flow = ISO_FLOW.get(start_emotion, ["Neutral"])
    playlist = []

    for emotion in flow:
        songs = load_songs(EMOTION_PATHS.get(emotion, ""))
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
        print("❌ No songs found")
        return

    # ✅ RUN MUSIC IN BACKGROUND
    threading.Thread(target=play_playlist_thread, args=(playlist,), daemon=True).start()
