import os
import pygame

# --------------------- Song Selection ---------------------
def select_song(emotion):
    """
    Selects a Malayalam song based on the detected emotion.
    Emotions: sad, happy, angry, surprised, neutral
    """
    emotion = emotion.lower()
    
    if emotion == "sad":
        return "audio/malayalam/malayalam_sad.mp3"
    elif emotion == "happy":
        return "audio/malayalam/malayalam_happy.mp3"
    elif emotion == "angry":
        return "audio/malayalam/malayalam_angry.mp3"
    elif emotion == "surprised":
        return "audio/malayalam/malayalam_surprised.mp3"
    else:  # neutral or unknown
        return "audio/malayalam/malayalam_calm.mp3"

# --------------------- Play Song ---------------------
def play_song(song_path):
    """
    Plays the given song using pygame.
    """
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
    # Simulate a pre-detected emotion from your system
    detected_emotion = "happy"  # Change this to test: sad, angry, surprised, neutral

    # Select the song
    song_file = select_song(detected_emotion)

    # Play the selected song
    play_song(song_file)
