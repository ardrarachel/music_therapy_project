import os
import requests

# Free sample music links (royalty-free demo tracks)
songs = {
    "neutral": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Scott_Holmes_Music/Corporate__Motivational_Music/Scott_Holmes_Music_-_04_-_Driven_To_Success.mp3"
    ],
    "happy": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Scott_Holmes_Music/Happy_Music/Scott_Holmes_Music_-_01_-_Happy_Days.mp3"
    ],
    "sad": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lee_Rosevere/Music_for_Podcasts_2/Lee_Rosevere_-_05_-_Sad_Marimba_Planet.mp3"
    ],
    "angry": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/BoxCat_Games/Nameless/BoxCat_Games_-_09_-_Battle_Boss.mp3"
    ],
    "surprised": [
        "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Komiku/Its_time_for_adventure/Komiku_-_03_-_Surprise.mp3"
    ]
}

base_path = "audio/malayalam"  # change to english/hindi/tamil if needed

for mood, links in songs.items():
    folder = os.path.join(base_path, mood)
    os.makedirs(folder, exist_ok=True)

    for i, url in enumerate(links):
        filename = os.path.join(folder, f"{mood}_{i+1}.mp3")
        print(f"Downloading {filename}...")
        r = requests.get(url)
        with open(filename, "wb") as f:
            f.write(r.content)

print("✅ Songs downloaded successfully!")
