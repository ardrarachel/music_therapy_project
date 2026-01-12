import pandas as pd

# Load dataset
df = pd.read_csv("tracks.csv")

# Keep only required features
df = df[["valence", "energy"]]

# Drop missing values
df = df.dropna()

# Save cleaned dataset
df.to_csv("tracks_cleaned.csv", index=False)

print("Saved tracks_cleaned.csv with only valence & energy")
print("Rows:", len(df))
