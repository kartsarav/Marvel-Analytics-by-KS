#date created: 11.25.2025
#date modified: 11.25.2025
import requests
import pandas as pd
import os
import time
import json
from tqdm import tqdm

# === PATH SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

INPUT_FILE = os.path.join(root_dir, "data", "processing", "filter 2", "csv", "filtered_movies.csv")
OUTPUT_FILE = os.path.join(root_dir, "data", "output", "csv", "imdb_attributes_movies.csv")
CACHE_FILE = os.path.join(root_dir, "data", "output", "csv", "imdb_attributes_cache.json")

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


def fetch_all_attributes(imdb_id):
    """Scrape ALL release attributes for a movie (multi-page)."""
    attributes = {}

    cursor = None

    while True:
        data = fetch_release_page(imdb_id, cursor)

        edges = data["data"]["title"]["releaseDates"]["edges"]
        page_info = data["data"]["title"]["releaseDates"]["pageInfo"]

        # Extract attributes
        for edge in edges:
            node = edge["node"]
            attrs = node.get("attributes", [])
            if len(attrs) == 0:
                label = "blank"
                attributes[label] = attributes.get(label, 0) + 1
            else:
                for a in attrs:
                    label = a["text"].strip().lower()
                    attributes[label] = attributes.get(label, 0) + 1

        # Stop if no more pages
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        time.sleep(0.2)

    return attributes


# === Load Input CSV ===
print("🔹 Loading movie list...")
df = pd.read_csv(INPUT_FILE)

# === Load Cache ===
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

# === Prepare Output Storage ===
results = []

print("🎬 Scraping IMDb attributes...")
for _, row in tqdm(df.iterrows(), total=len(df)):
    title = str(row["title"])
    imdb_id = str(row["imdb_id"])

    # Skip missing IMDb IDs
    if imdb_id == "" or imdb_id.lower() == "nan":
        results.append({"title": title, "attributes": ""})
        continue

    # Cache hit
    if imdb_id in cache:
        attributes = cache[imdb_id]  # now a dict of counts
    else:
        try:
            attributes = fetch_all_attributes(imdb_id)
        except Exception as e:
            print(f"⚠️ Error fetching {imdb_id}: {e}")
            attributes = {}

        cache[imdb_id] = attributes

    results.append({
        "title": title,
        "attributes": ", ".join([f"{label} ({count})" for label, count in attributes.items()])
    })

# === Save Cache ===
with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)

# === Save Output CSV ===
output_df = pd.DataFrame(results)
output_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Done! Saved IMDb attributes to: {OUTPUT_FILE}")