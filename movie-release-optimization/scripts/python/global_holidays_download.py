# date created: 12.16.2025
# date modified: 12.16.2025
# description: Script to download global holidays data from a public API and save it as a CSV
# date created: 12.16.2025
# description: Download global holidays using Calendarific API

import requests
import csv
import time
import os
from tqdm import tqdm

# === PATHS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
OUTPUT_FILE = os.path.join(root_dir, "data", "output", "csv", "global_holidays.csv")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# === CALENDARIFIC SETTINGS ===
API_KEY = "XFsw99gu4QwJaw1bsWhm6AIKQdVSkSQo"
BASE_URL = "https://calendarific.com/api/v2/holidays"

START_YEAR = 2008
END_YEAR = 2025

COUNTRY_CODES = [
    "US", "IN", "GB", "CA", "AU", "NZ",
    "CN", "JP", "KR",
    "DE", "FR", "IT"
]

FIELDNAMES = [
    "date",
    "year",
    "country_code",
    "name",
    "description",
    "primary_type",
    "types",
    "locations",
    "states",
    "source"
]

rows = []

# === DOWNLOAD LOOP ===
for country in tqdm(COUNTRY_CODES, desc="Countries", unit="country"):
    for year in tqdm(range(START_YEAR, END_YEAR + 1),
                     desc=f"Years ({country})",
                     leave=False,
                     unit="year"):

        params = {
            "api_key": API_KEY,
            "country": country,
            "year": year
        }

        try:
            r = requests.get(BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            holidays = data.get("response", {}).get("holidays", [])
            if not holidays:
                continue

        except Exception as e:
            print(f"⚠️ Failed {country} {year}: {e}")
            continue

        for h in holidays:
            rows.append({
                "date": h["date"]["iso"],
                "year": year,
                "country_code": country,
                "name": h.get("name"),
                "description": h.get("description"),
                "primary_type": h.get("primary_type"),
                "types": "|".join(h.get("type", [])),
                "locations": h.get("locations"),
                "states": h.get("states"),
                "source": "calendarific"
            })

        # Polite rate limiting
        time.sleep(0.3)

# === WRITE CSV ===
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Holidays saved to {OUTPUT_FILE}")