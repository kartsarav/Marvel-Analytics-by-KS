# date created: 02.15.2026
# Scrapes IMDb release countries for each movie

import requests
import pandas as pd
import os
import time
import json
from tqdm import tqdm

# === PATH SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

INPUT_FILE = os.path.join(
    root_dir,
    "data",
    "processing",
    "filter 3",
    "csv",
    "imdb_attributes_movies_required_copy.csv"
)

OUTPUT_FILE = os.path.join(
    root_dir,
    "data",
    "output",
    "csv",
    "imdb_release_countries_movies.csv"
)

CACHE_FILE = os.path.join(
    root_dir,
    "data",
    "output",
    "csv",
    "imdb_release_countries_cache.json"
)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# === IMDb GraphQL API ===
IMDB_GRAPHQL_URL = "https://caching.graphql.imdb.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

PERSISTED_HASH = "0e4e6468b8bc55114f80551e7a062301c78999ee538789a936902e4ab5239ccd"


def fetch_release_page(imdb_id, cursor=None):
    """Fetch one page of IMDb release info using GraphQL."""
    variables = {
        "const": imdb_id,
        "first": 50,
        "locale": "en-US",
        "originalTitleText": False
    }

    if cursor:
        variables["after"] = cursor

    payload = {
        "operationName": "TitleReleaseDatesPaginated",
        "variables": variables,
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": PERSISTED_HASH
            }
        }
    }

    headers = HEADERS.copy()
    headers["Content-Type"] = "application/json"

    response = requests.post(IMDB_GRAPHQL_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_all_countries(imdb_id):
    """Scrape ALL release countries for a movie (multi-page)."""
    countries = set()
    cursor = None

    while True:
        data = fetch_release_page(imdb_id, cursor)

        if (
            not isinstance(data, dict)
            or "data" not in data
            or data["data"] is None
            or "title" not in data["data"]
        ):
            raise Exception(
                f"Unexpected response structure for {imdb_id}: {str(data)[:300]}"
            )

        edges = data["data"]["title"]["releaseDates"]["edges"]
        page_info = data["data"]["title"]["releaseDates"]["pageInfo"]

        for edge in edges:
            node = edge["node"]
            country_obj = node.get("country")
            if country_obj and "text" in country_obj:
                countries.add(country_obj["text"].strip())

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        time.sleep(0.2)

    return sorted(list(countries))


# === Load Input CSV ===
print("🔹 Loading movie list...")
df = pd.read_csv(INPUT_FILE)

# === Load Cache ===
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

results = []

print("🌍 Scraping IMDb release countries...")
for _, row in tqdm(
    df.iterrows(),
    total=len(df),
    desc="Scraping IMDb release countries",
    unit="movie"
):
    title = str(row["title"])
    imdb_id = str(row["imdb_id"])

    error_flag = False

    if imdb_id == "" or imdb_id.lower() == "nan":
        row_data = row.to_dict()
        row_data.update({
            "release_countries": "",
            "country_count": 0,
            "error": "no"
        })
        results.append(row_data)
        continue

    # Cache hit
    if imdb_id in cache:
        countries = cache[imdb_id]
    else:
        countries = None
        for attempt in range(1, 4):
            try:
                countries = fetch_all_countries(imdb_id)
                break
            except Exception as e:
                print(f"⚠️ Error fetching {imdb_id} (attempt {attempt}/3): {e}")
                if attempt < 3:
                    sleep_time = 1.5 * attempt
                    print(f"   → retrying after {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    print(
                        f"   → failed to fetch {imdb_id} after 3 attempts, recording empty countries."
                    )
                    error_flag = True

        if countries is None:
            countries = []

        cache[imdb_id] = countries

    row_data = row.to_dict()
    row_data.update({
        "release_countries": ", ".join(countries),
        "country_count": len(countries),
        "error": "yes" if error_flag else "no"
    })

    results.append(row_data)

# === Save Cache ===
with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)

# === Save Output CSV ===
output_df = pd.DataFrame(results)
output_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Done! Saved IMDb release countries to: {OUTPUT_FILE}")