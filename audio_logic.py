import os
import random
import pygame
import threading
import time

# Initialize mixer safely
def init_player():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

# Base folder for music
BASE_PATH = os.path.join(os.getcwd(), "audio", "malayalam")

# Emotion progression (ISO principle)
ISO_FLOW = {
    "Sad": ["Sad", "Neutral", "Happy"],
    "Angry": ["Angry", "Neutral", "Happy"],
    "Neutral": ["Neutral", "Happy"],
    "Happy": ["Happy"],
    "Surprised": ["Surprised", "Happy"]
}

# Map each emotion to its folder
EMOTION_PATHS = {
    emotion: os.path.join(BASE_PATH, emotion.lower())
    for emotion in ["Sad", "Angry", "Neutral", "Happy", "Surprised"]
}

def load_songs(folder):
    print(f"🔍 Loading songs from folder: {folder}")

    if not os.path.exists(folder):
        print(f"⚠ Folder missing: {folder}")
        return []

    songs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith((".mp3", ".mpeg"))
    ]

    print(f"🎵 Found songs: {songs}")
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


def play_playlist(playlist):
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

    threading.Thread(target=play_playlist, args=(playlist,), daemon=True).start()
