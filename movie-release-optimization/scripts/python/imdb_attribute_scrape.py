#date created: 11.25.2025
#date modified: 02.17.2026
import requests
import pandas as pd
import os
import time
import json
from tqdm import tqdm
import re
pattern = re.compile(r"([a-zA-Z]+)\s*\((\d+)\)")

def parse_counts(attr_dict):
    blank_count = 0
    internet_count = 0
    total_count = 0

    if not isinstance(attr_dict, dict):
        return blank_count, internet_count, total_count

    for label, count in attr_dict.items():
        label = label.strip().lower()
        total_count += count
        if label == "blank":
            blank_count = count
        elif label == "internet":
            internet_count = count

    return blank_count, internet_count, total_count

# === PATH SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

MARVEL_FILE = os.path.join(root_dir, "data", "processing", "filter 1", "csv", "scrape_marvel_movies.csv")
COMPETITION_DIR = os.path.join(root_dir, "data", "processing", "filter 2", "csv", "competition")
OUTPUT_DIR = os.path.join(root_dir, "data", "output", "csv")

CACHE_FILE = os.path.join(root_dir, "data", "output", "csv", "imdb_attributes_cache.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

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

        # Defensive check -- sometimes IMDb returns unexpected JSON
        if not isinstance(data, dict) or "data" not in data or data["data"] is None or "title" not in data["data"]:
            raise Exception(f"Unexpected response structure for {imdb_id}: {str(data)[:300]}")

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


# === Load Marvel Master List ===
print("🔹 Loading Marvel master list...")
marvel_df = pd.read_csv(MARVEL_FILE)

if "title" not in marvel_df.columns:
    raise RuntimeError("Marvel file must contain a 'title' column.")

# === Load Cache ===
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

# === Process Each Marvel Competition File ===
for _, mrow in marvel_df.iterrows():

    marvel_title = str(mrow["title"]).strip()
    safe_title = marvel_title.replace(" ", "_")

    input_path = os.path.join(COMPETITION_DIR, f"{safe_title}_competition.csv")

    if not os.path.exists(input_path):
        raise RuntimeError(f"Missing competition file: {input_path}")

    print(f"\n🎬 Processing competition file for: {marvel_title}")
    df = pd.read_csv(input_path)

    results = []

    for _, row in tqdm(
        df.iterrows(),
        total=len(df),
        desc=f"Scraping IMDb release attributes ({marvel_title})",
        unit="movie"
    ):
        title = str(row.get("title", ""))
        imdb_id = str(row.get("imdb_id", ""))

        error_flag = False

        if imdb_id == "" or imdb_id.lower() == "nan":
            row_data = row.to_dict()
            row_data.update({"attributes": "", "error": "no"})
            results.append(row_data)
            continue

        if imdb_id in cache:
            attributes = cache[imdb_id]
        else:
            attributes = None
            for attempt in range(1, 4):
                try:
                    attributes = fetch_all_attributes(imdb_id)
                    break
                except Exception as e:
                    print(f"⚠️ Error fetching {imdb_id} (attempt {attempt}/3): {e}")
                    if attempt < 3:
                        sleep_time = 1.5 * attempt
                        print(f"   → retrying after {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        print(f"   → failed after 3 attempts.")
                        error_flag = True
            if attributes is None:
                attributes = {}
            cache[imdb_id] = attributes

        blank_c, internet_c, total_c = parse_counts(attributes)

        internet_ratio = round(internet_c / total_c, 2) if total_c > 0 else 0
        internet_dominance = "yes" if internet_c > blank_c else "no"

        row_data = row.to_dict()
        row_data.update({
            "attributes": ", ".join([f"{label} ({count})" for label, count in attributes.items()]),
            "blank": blank_c,
            "internet": internet_c,
            "total": total_c,
            "internet_ratio": internet_ratio,
            "internet_dominance": internet_dominance,
            "error": "yes" if error_flag else "no"
        })

        results.append(row_data)

    output_df = pd.DataFrame(results)
    output_path = os.path.join(OUTPUT_DIR, f"{safe_title}_attributes.csv")
    output_df.to_csv(output_path, index=False)

    print(f"✅ Saved attributes file: {output_path}")

# === Save Cache After All Movies ===
with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)

print("\n✅ All Marvel competition files processed successfully.")