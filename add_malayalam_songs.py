import pandas as pd

# Load existing dataset
df = pd.read_csv("tracks_with_mood.csv", low_memory=False)

# Create a new DataFrame for Malayalam songs
malayalam_songs = pd.DataFrame([
    {"track_id": "M001", "artists": "Artist1", "album_name": "Album1", "track_name": "Song1",
     "duration_ms": 200000, "energy": 0.5, "valence": 0.6, "track_genre": "malayalam", "mood": "happy"},
    {"track_id": "M002", "artists": "Artist2", "album_name": "Album2", "track_name": "Song2",
     "duration_ms": 180000, "energy": 0.3, "valence": 0.2, "track_genre": "malayalam", "mood": "sad"}
])

# Combine old dataset with new Malayalam songs
df = pd.concat([df, malayalam_songs], ignore_index=True)

# Save updated CSV
df.to_csv("tracks_with_mood.csv", index=False)

print("Updated tracks_with_mood.csv with Malayalam songs successfully!")
