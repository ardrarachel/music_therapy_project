import pandas as pd

# Load dataset
df = pd.read_csv("tracks.csv", low_memory=False)

print("Original columns:", df.columns)

# Columns to remove
cols_to_drop = [
    "popularity",
    "explicit",
    "danceability",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "tempo",
    "time_signature"
]

# Drop the columns
df = df.drop(columns=cols_to_drop)

print("Remaining columns:", df.columns)

# Save cleaned dataset
df.to_csv("tracks_cleaned.csv", index=False)

print("tracks_cleaned.csv created successfully")
