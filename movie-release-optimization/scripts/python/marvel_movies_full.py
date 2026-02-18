# created: 12.16.2025
# modified: 12.16.2025
# description: Script to get a list of marvel movies and its data from movie list

# date created: 12.16.2025
# description: Extract full Marvel movie rows from all_movies_file using title matching

import pandas as pd
import os

# === PATH SETUP ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

ALL_MOVIES_FILE = os.path.join(
    root_dir, "data", "processing", "filter 1", "csv", "movies.csv"
)

MARVEL_MOVIES_FILE = os.path.join(
    root_dir, "data", "processing", "filter 1", "csv", "marvel_movies.csv"
)

OUTPUT_FILE = os.path.join(
    root_dir, "data", "output", "csv", "marvel_movies_full.csv"
)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# === LOAD CSV FILES ===
print("🔹 Loading CSV files...")
all_movies = pd.read_csv(ALL_MOVIES_FILE)
marvel_movies = pd.read_csv(MARVEL_MOVIES_FILE)

# === VALIDATION ===
required_column = "title"

if required_column not in all_movies.columns:
    raise ValueError("❌ 'title' column missing from all_movies_file")

if required_column not in marvel_movies.columns:
    raise ValueError("❌ 'title' column missing from marvel_movies_file")

# === GET MARVEL TITLE LIST ===
marvel_titles = (
    marvel_movies["title"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

print(f"🎬 Found {len(marvel_titles)} Marvel titles")

# === FILTER ALL MOVIES ===
marvel_full_df = all_movies[
    all_movies["title"].astype(str).str.strip().isin(marvel_titles)
].copy()

# === REMOVE DUPLICATES (SAFETY) ===
marvel_full_df = marvel_full_df.drop_duplicates(subset=["title"])

# === SAVE OUTPUT ===
marvel_full_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved {len(marvel_full_df)} Marvel movies to:")
print(OUTPUT_FILE)