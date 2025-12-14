# Project: Marvel Analytics by KS - Movie Release Optimization
# File: filter_movies.py
# Author: Kartik Saravanan
# Date: NOV 12 2025
# Last Modified: DEC 13 2025
# Description: Filters a large movie list to find movies released in the same month or same ISO week around each Marvel movie.
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


# === STEP 2: DATE WINDOW FILTERING ===
print("🔹 Filtering movies within same month or week of each Marvel movie release...")
filtered_list = []

for _, mrow in marvel_movies.iterrows():
    marvel_title = mrow["title_clean"]

    marvel_row = all_movies[all_movies["title_clean"] == marvel_title]

    if marvel_row.empty:
        print(f"❌ ERROR: Marvel movie '{marvel_title}' not found in all_movies.csv")
        raise RuntimeError("Marvel title missing from all_movies")

    marvel_year = marvel_row.iloc[0]["release_year"]
    marvel_month = marvel_row.iloc[0]["release_month"]
    marvel_week = marvel_row.iloc[0]["iso_week"]

    marvel_imdb_votes = marvel_row.iloc[0].get("imdb_votes", None)
    marvel_popularity = marvel_row.iloc[0].get("popularity", None)

    nearby = all_movies[
        (
            (all_movies["release_year"] == marvel_year) &
            (all_movies["release_month"] == marvel_month)
        )
        |
        (
            (all_movies["release_year"] == marvel_year) &
            (all_movies["iso_week"] == marvel_week)
        )
    ].copy()


    # === STEP 3: APPLY DYNAMIC COMPETITOR FILTERS ===
    if marvel_imdb_votes is None or pd.isna(marvel_imdb_votes) or marvel_popularity is None or pd.isna(marvel_popularity):
        print(f"⚠️ WARNING: Missing IMDb votes or popularity for Marvel movie '{marvel_title}'. Skipping dynamic filters.")
    else:
        vote_threshold = marvel_imdb_votes * VOTE_FACTOR
        pop_threshold = marvel_popularity * POPULARITY_FACTOR

        nearby = nearby[
            (nearby["imdb_votes"] >= vote_threshold) &
            (nearby["popularity"] >= pop_threshold)
        ]

    # Ensure imdb_id column is preserved and cast to string
    if "imdb_id" in nearby.columns:
        nearby["imdb_id"] = nearby["imdb_id"].astype(str)
    else:
        print("⚠️ WARNING: imdb_id column missing in movies.csv!")

    # === STEP 4: FILTER OUT STREAMING-ONLY RELEASES (production_companies) ===
    if "production_companies" in nearby.columns:
        nearby["production_companies"] = nearby["production_companies"].fillna("").astype(str).str.lower()
        pattern = "|".join([kw.replace("+", "\\+") for kw in STREAMING_KEYWORDS])
        nearby = nearby[~nearby["production_companies"].str.contains(pattern, regex=True)]

    if not nearby.empty:
        nearby["marvel_movie"] = marvel_title
        filtered_list.append(nearby)


# === COMBINE RESULTS ===
if filtered_list:
    filtered_movies = pd.concat(filtered_list, ignore_index=True)
else:
    print("⚠️ No movies passed both filters.")
    filtered_movies = pd.DataFrame(columns=list(all_movies.columns) + ["marvel_movie"])


# === MERGE MULTIPLE MARVEL MATCHES ===
print("🔹 Merging duplicate movies...")

def merge_unique(values):
    unique_vals = sorted(set(values))
    return ", ".join(map(str, unique_vals))

filtered_movies = (
    filtered_movies
    .groupby("title", as_index=False)
    .agg({
        **{col: "first" for col in filtered_movies.columns if col != "marvel_movie"},
        "marvel_movie": merge_unique
    })
)

# === SAVE OUTPUT ===
os.makedirs(os.path.dirname(output_file), exist_ok=True)
filtered_movies.to_csv(output_file, index=False)

print(f"✅ Filtering complete! {len(filtered_movies)} movies saved to '{output_file}'.")