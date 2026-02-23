import pandas as pd

# Load cleaned dataset
df = pd.read_csv("tracks_cleaned.csv")

def classify_mood(row):
    valence = row["valence"]
    energy = row["energy"]

    if valence >= 0.6 and energy >= 0.6:
        return "happy"
    elif valence <= 0.4 and energy <= 0.4:
        return "sad"
    elif valence <= 0.4 and energy >= 0.6:
        return "angry"
    elif valence >= 0.6 and 0.4 <= energy < 0.6:
        return "surprised"
    else:
        return "neutral"

# Apply mood classification
df["mood"] = df.apply(classify_mood, axis=1)

# Save final dataset
df.to_csv("tracks_with_mood.csv", index=False)

print("tracks_with_mood.csv created with mood labels")
# Assuming 'df' is your DataFrame after adding the mood column
df.to_csv("tracks_with_mood.csv", index=False)
print("tracks_with_mood.csv created successfully")
