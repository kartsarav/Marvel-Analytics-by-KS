# Project: Marvel Analytics by KS - Movie Release Optimization
# File: filter_movies.py
# Author: Kartik Saravanan
# Date: NOV 12 2025
# Last Modified: FEB 17 2025
# Description: Filters a large movie list to find movies released in the same month or same ISO week around each Marvel movie.
# Supports multiple Marvel matches per movie entry.

import pandas as pd
import numpy as np
from datetime import timedelta
import os

# === SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

all_movies_file = os.path.join(root_dir, "data", "processing", "filter 1", "csv", "movies.csv")
marvel_movies_file = os.path.join(root_dir, "data", "processing", "filter 1", "csv", "scrape_marvel_movies.csv")
output_dir = os.path.join(root_dir, "data", "output", "csv")

VOTE_FACTOR = 0.1
POPULARITY_FACTOR = 0.15

# === STREAMING SERVICE KEYWORDS (GLOBAL) ===
STREAMING_KEYWORDS = [
    # US majors
    "netflix", "amazon", "prime video", "apple", "disney+", "hulu",
    "hbo", "max original", "peacock", "paramount+",

    # India
    "hotstar", "zee5", "sonyliv", "jio cinema", "aha", "sun nxt",
    "mx player", "eros now", "voot", "hoichoi",

    # Korea
    "tving", "wavve", "coupang", "kakao",

    # Japan
    "u-next", "abema", "wowow",

    # China
    "iqiyi", "youku", "tencent", "bilibili",

    # Europe / LatAm
    "sky studios", "viaplay", "canal+", "movistar+", "atresplayer",
    "clarovideo"
]


# === LOAD DATA ===
print("🔹 Loading CSV files...")
all_movies = pd.read_csv(all_movies_file)
marvel_movies = pd.read_csv(marvel_movies_file)

# Normalize column names
all_movies.columns = all_movies.columns.str.strip().str.lower()
marvel_movies.columns = marvel_movies.columns.str.strip().str.lower()

all_movies["title_clean"] = all_movies["title"].str.lower().str.strip()
marvel_movies["title_clean"] = marvel_movies["title"].str.lower().str.strip()

# === VALIDATE REQUIRED DATE COLUMNS EXIST ===
required_cols = ["release_year", "release_month", "iso_week"]

missing_all = [c for c in required_cols if c not in all_movies.columns]

if missing_all:
    print(f"❌ ERROR: all_movies is missing columns: {missing_all}")
    raise RuntimeError("Required release date columns missing. Fix CSV files before running.")

# Drop any rows in marvel_movies with missing titles
if marvel_movies["title_clean"].isna().any():
    bad_rows = marvel_movies[marvel_movies["title_clean"].isna()]
    print("❌ ERROR: Marvel movies file contains rows with missing titles:")
    print(bad_rows)
    raise RuntimeError("Fix missing Marvel titles before continuing.")


# === STEP 2: DISTANCE-BASED COMPETITION ANALYSIS ===
print("🔹 Computing distance-based competition for each Marvel movie...")

# Ensure release_date is datetime
all_movies["release_date"] = pd.to_datetime(all_movies["release_date"], errors="coerce")

if all_movies["release_date"].isna().any():
    print("❌ ERROR: Some release_date values could not be parsed.")
    raise RuntimeError("Fix release_date column before continuing.")

os.makedirs(output_dir, exist_ok=True)

for _, mrow in marvel_movies.iterrows():
    marvel_title = mrow["title_clean"]

    marvel_row = all_movies[all_movies["title_clean"] == marvel_title]

    if marvel_row.empty:
        print(f"❌ ERROR: Marvel movie '{marvel_title}' not found in all_movies.csv")
        raise RuntimeError("Marvel title missing from all_movies")

    marvel_release_date = marvel_row.iloc[0]["release_date"]

    # Copy full dataset
    competitors = all_movies.copy()

    # Exclude the Marvel movie itself
    competitors = competitors[competitors["title_clean"] != marvel_title]

    # Compute signed distance in days
    competitors["distance"] = (
        competitors["release_date"] - marvel_release_date
    ).dt.days

    # Keep only realistic theatrical competition window (±45 days)
    competitors = competitors[competitors["distance"].abs() <= 45]

    # Remove streaming-only releases
    if "production_companies" in competitors.columns:
        competitors["production_companies"] = competitors["production_companies"].fillna("").astype(str).str.lower()
        pattern = "|".join([kw.replace("+", "\\+") for kw in STREAMING_KEYWORDS])
        competitors = competitors[~competitors["production_companies"].str.contains(pattern, regex=True)]

    # Compute strength using log revenue
    if "revenue" in competitors.columns:
        competitors["revenue"] = pd.to_numeric(competitors["revenue"], errors="coerce").fillna(0)
        competitors["strength"] = np.log1p(competitors["revenue"])
    else:
        print("❌ ERROR: revenue column missing in movies.csv")
        raise RuntimeError("Revenue column required for strength calculation")

    # Compute competition score (distance decay)
    competitors["score"] = competitors["strength"] / (1 + competitors["distance"].abs())

    # Keep Marvel movie reference
    competitors["marvel_movie"] = marvel_title

    # Generate per-Marvel output file
    safe_title = marvel_title.replace(" ", "_")
    output_file = os.path.join(output_dir, f"{safe_title}_competition.csv")

    competitors.to_csv(output_file, index=False)

    print(f"✅ Saved competition file for '{marvel_title}' to '{output_file}'")