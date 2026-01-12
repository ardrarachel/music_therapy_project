import pandas as pd

# Load the dataset
df = pd.read_csv("tracks.csv")

# Check if file loaded correctly
print("Rows loaded:", len(df))
print("Columns:", df.columns)

# Clean / filter data
df = df.dropna(subset=["valence", "energy"])

# Check after cleaning
print("Rows after cleaning:", len(df))

# Save the cleaned dataset
df.to_csv("tracks_cleaned.csv", index=False)
print("Cleaned dataset saved as tracks_cleaned.csv")
