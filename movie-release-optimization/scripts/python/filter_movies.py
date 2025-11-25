# Project: Marvel Analytics by KS - Movie Release Optimization
# File: filter_movies.py
# Author: Kartik Saravanan
# Date: NOV 12 2025
# Last Modified: NOV 14 2025
# Description: Filters a large movie list to find movies released ±60 days around each Marvel movie.
# Supports multiple Marvel matches per movie entry.

import pandas as pd
from datetime import timedelta
import os

# === SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

all_movies_file = os.path.join(root_dir, "data", "processing", "filter 1", "csv", "movies.csv")
marvel_movies_file = os.path.join(root_dir, "data", "processing", "filter 1", "csv", "marvel_movies.csv")
output_file = os.path.join(root_dir, "data", "output", "csv", "filtered_movies.csv")

date_window = 60  # days before/after Marvel release
VOTE_FACTOR = 0.1
POPULARITY_FACTOR = 0.15


# === LOAD DATA ===
print("🔹 Loading CSV files...")
all_movies = pd.read_csv(all_movies_file)
marvel_movies = pd.read_csv(marvel_movies_file)

# Normalize column names
all_movies.columns = all_movies.columns.str.strip().str.lower()
marvel_movies.columns = marvel_movies.columns.str.strip().str.lower()

# Convert release dates
all_movies["release_date"] = pd.to_datetime(all_movies["release_date"], errors="coerce")
marvel_movies["release_date"] = pd.to_datetime(marvel_movies["release_date"], errors="coerce")

all_movies = all_movies.dropna(subset=["release_date"])
marvel_movies = marvel_movies.dropna(subset=["release_date"])

# === STEP 1: Enrich Marvel movies with imdb_votes + popularity ===
print("🔹 Enriching Marvel movie list with IMDb votes and popularity...")

lookup = all_movies[["title", "imdb_votes", "popularity"]].copy()
lookup["title"] = lookup["title"].str.lower().str.strip()

marvel_movies["title_clean"] = marvel_movies["title"].str.lower().str.strip()

# LEFT JOIN using title
marvel_movies = marvel_movies.merge(
    lookup,
    left_on="title_clean",
    right_on="title",
    how="left",
    suffixes=("", "_all")
)

# Cleanup
marvel_movies.rename(columns={
    "imdb_votes": "marvel_imdb_votes",
    "popularity": "marvel_popularity"
}, inplace=True)

marvel_movies.drop(columns=["title", "title_all"], errors="ignore", inplace=True)

# Warn if some Marvel movies were not found
missing_stats = marvel_movies[marvel_movies["marvel_imdb_votes"].isna()]
if not missing_stats.empty:
    print("⚠️ WARNING: Some Marvel movies missing vote/popularity data:")
    print(missing_stats[["title_clean"]])

# Fill missing with 0 to avoid crashes
marvel_movies["marvel_imdb_votes"] = marvel_movies["marvel_imdb_votes"].fillna(0)
marvel_movies["marvel_popularity"] = marvel_movies["marvel_popularity"].fillna(0)


# === STEP 2: DATE WINDOW FILTERING ===
print("🔹 Filtering movies within ±60 days of each Marvel release...")
filtered_list = []

for _, mrow in marvel_movies.iterrows():
    marvel_title = mrow["title_clean"]
    marvel_date = mrow["release_date"]

    start = marvel_date - timedelta(days=date_window)
    end = marvel_date + timedelta(days=date_window)

    # Base filter: Date range
    nearby = all_movies[
        (all_movies["release_date"] >= start) &
        (all_movies["release_date"] <= end)
    ].copy()

    if nearby.empty:
        continue

    # === STEP 3: APPLY DYNAMIC COMPETITOR FILTERS ===
    vote_threshold = mrow["marvel_imdb_votes"] * VOTE_FACTOR
    pop_threshold = mrow["marvel_popularity"] * POPULARITY_FACTOR

    nearby = nearby[
        (nearby["imdb_votes"] >= vote_threshold) &
        (nearby["popularity"] >= pop_threshold)
    ]

    if not nearby.empty:
        nearby["marvel_movie"] = marvel_title
        nearby["marvel_release_date"] = marvel_date.strftime("%Y-%m-%d")
        filtered_list.append(nearby)


# === COMBINE RESULTS ===
if filtered_list:
    filtered_movies = pd.concat(filtered_list, ignore_index=True)
else:
    print("⚠️ No movies passed both filters.")
    filtered_movies = pd.DataFrame(columns=["title", "marvel_movie", "marvel_release_date"])


# === MERGE MULTIPLE MARVEL MATCHES ===
print("🔹 Merging duplicate movies...")

def merge_unique(values):
    unique_vals = sorted(set(values))
    return ", ".join(map(str, unique_vals))

filtered_movies = (
    filtered_movies.groupby("title", as_index=False)
    .agg({
        "marvel_movie": merge_unique,
        "marvel_release_date": merge_unique
    })
)

# === SAVE OUTPUT ===
os.makedirs(os.path.dirname(output_file), exist_ok=True)
filtered_movies.to_csv(output_file, index=False)

print(f"✅ Filtering complete! {len(filtered_movies)} movies saved to '{output_file}'.")