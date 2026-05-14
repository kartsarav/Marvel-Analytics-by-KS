# Project: Marvel Analytics by KS - Movie Release Optimization
# File: holiday_proximity_per_movie.py
# date created: 02.16.2026
# Description:
# For each Marvel movie, compute holiday proximity tiers
# and output one CSV per movie.

import pandas as pd
import os
import re

# === PATH SETUP ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

global_holidays_file = os.path.join(
    root_dir, "data", "processing", "filter 1", "csv", "global_holidays.csv"
)

marvel_movies_file = os.path.join(
    root_dir, "data", "processing", "filter 1", "csv", "scrape_marvel_movies.csv"
)

output_dir = os.path.join(
    root_dir, "data", "output", "csv", "holiday_proximity"
)

os.makedirs(output_dir, exist_ok=True)

# === LOAD DATA ===
print("🔹 Loading datasets...")

holidays = pd.read_csv(global_holidays_file)
marvel_movies = pd.read_csv(marvel_movies_file)

# Normalize column names
holidays.columns = holidays.columns.str.strip().str.lower()
marvel_movies.columns = marvel_movies.columns.str.strip().str.lower()

# Validate required columns
required_holiday_cols = [
    "date", "country_code", "name",
    "primary_type", "types", "strength"
]

missing_cols = [c for c in required_holiday_cols if c not in holidays.columns]
if missing_cols:
    raise RuntimeError(f"❌ Missing columns in global_holidays.csv: {missing_cols}")

if "title" not in marvel_movies.columns or "release_date" not in marvel_movies.columns:
    raise RuntimeError("❌ Marvel movies file must contain 'title' and 'release_date' columns")

# Force consistent datetime dtype (handle timezone-aware values safely)
holidays["date"] = pd.to_datetime(
    holidays["date"],
    errors="coerce",
    utc=True
).dt.tz_convert(None)

marvel_movies["release_date"] = pd.to_datetime(
    marvel_movies["release_date"],
    errors="coerce",
    utc=True
).dt.tz_convert(None)

holidays = holidays.dropna(subset=["date"])
marvel_movies = marvel_movies.dropna(subset=["release_date"])

print(f"🔹 Processing {len(marvel_movies)} Marvel movies...")

# === PROXIMITY FUNCTION ===
def calculate_proximity(days_diff):
    days_diff = abs(days_diff)

    if days_diff <= 3:
        return 3
    elif days_diff <= 7:
        return 2
    elif days_diff <= 14:
        return 1
    else:
        return 0

# === LOOP THROUGH EACH MARVEL MOVIE ===
for _, row in marvel_movies.iterrows():

    title = row["title"]
    release_date = row["release_date"]

    print(f"🔹 Calculating proximity for: {title}")

    # Create copy of relevant holiday columns only
    movie_holidays = holidays[required_holiday_cols].copy()

    # Ensure datetime type (robust guard inside loop)
    movie_holidays["date"] = pd.to_datetime(movie_holidays["date"], errors="coerce")

    # Compute days difference
    movie_holidays["days_from_release"] = (
        movie_holidays["date"] - pd.Timestamp(release_date)
    ).dt.days

    # Apply proximity tier
    movie_holidays["proximity"] = movie_holidays["days_from_release"].apply(calculate_proximity)

    # Drop intermediate column
    movie_holidays = movie_holidays.drop(columns=["days_from_release"])

    # Clean filename (remove special characters)
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = safe_title.strip().replace(" ", "_")

    output_file = os.path.join(
        output_dir,
        f"{safe_title}_holiday_proximity.csv"
    )

    movie_holidays.to_csv(output_file, index=False)

    print(f"   ✅ Saved: {output_file}")

print("🎯 All Marvel movie proximity files generated successfully.")