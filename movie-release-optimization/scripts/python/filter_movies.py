# Project: Marvel Analytics by KS - Movie Release Optimization
# File: filter_movies.py
# Author: Kartik Saravanan
# Date: NOV 12 2025
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

# === LOAD DATA ===
print("🔹 Loading CSV files...")
all_movies = pd.read_csv(all_movies_file)
marvel_movies = pd.read_csv(marvel_movies_file)

# Normalize column names
all_movies.columns = all_movies.columns.str.strip().str.lower()
marvel_movies.columns = marvel_movies.columns.str.strip().str.lower()

# === Convert release dates to datetime ===
all_movies["release_date"] = pd.to_datetime(all_movies["release_date"], errors="coerce")
marvel_movies["release_date"] = pd.to_datetime(marvel_movies["release_date"], errors="coerce")

# Drop invalid dates
all_movies = all_movies.dropna(subset=["release_date"])
marvel_movies = marvel_movies.dropna(subset=["release_date"])

# === FILTER LOGIC ===
print("🔹 Filtering movies within ±60 days of each Marvel release...")
filtered_list = []

for _, mrow in marvel_movies.iterrows():
    marvel_title = mrow["title"]
    marvel_date = mrow["release_date"]
    start = marvel_date - timedelta(days=date_window)
    end = marvel_date + timedelta(days=date_window)

    nearby = all_movies[
        (all_movies["release_date"] >= start) &
        (all_movies["release_date"] <= end)
    ].copy()

    if not nearby.empty:
        nearby["marvel_movie"] = marvel_title
        nearby["marvel_release_date"] = marvel_date.strftime("%Y-%m-%d")
        filtered_list.append(nearby)

# Combine all matched movies
if filtered_list:
    filtered_movies = pd.concat(filtered_list, ignore_index=True)
else:
    print("⚠️ No movies found within the specified date range.")
    filtered_movies = pd.DataFrame(columns=["title", "marvel_movie", "marvel_release_date"])

# === MERGE MULTIPLE MARVEL MATCHES PER MOVIE ===
print("🔹 Merging duplicate movies with multiple Marvel matches...")

def merge_unique(values):
    """Combine unique values into a comma-separated string."""
    unique_vals = sorted(set(values))
    return ", ".join(map(str, unique_vals))

filtered_movies = (
    filtered_movies.groupby("title", as_index=False)
    .agg({
        "marvel_movie": merge_unique,
        "marvel_release_date": merge_unique
    })
)

# === SAVE TO CSV ===
os.makedirs(os.path.dirname(output_file), exist_ok=True)
filtered_movies.to_csv(output_file, index=False)
print(f"✅ Filtering complete! {len(filtered_movies)} movies saved to '{output_file}'.")