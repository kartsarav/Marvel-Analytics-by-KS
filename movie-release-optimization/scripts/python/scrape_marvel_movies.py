# Project: Marvel Analytics by KS: Movie Release Optimization
# File: scrape_marvel_movies.py
# Author: Kartik Saravanan
# Date: NOV 12 2025
# Last Modified: NOV 14 2025
# Description: This script scrapes Marvel Cinematic Universe movie release data from Wikipedia
#              and saves it as a CSV file for the Marvel Analytics by KS: Movie Release Optimization project.

"""
Marvel Movie Data Scraper using Wikipedia API and Pandas
---------------------------------------------------------
This script fetches MCU movie data from Wikipedia safely using the Wikipedia API.
It avoids direct HTML scraping (403 errors) by using the API's parsed HTML content.

Author: [Your Name]
Date Created: Nov 2025
Last Modified: (auto-update manually as needed)
Requirements:
    pip install pandas wikipedia-api lxml requests
Output:
    marvel_movies.csv
"""

import os
import pandas as pd
import wikipediaapi
import requests

# Step 1 — Initialize Wikipedia API with custom user agent
USER_AGENT = "MarvelAnalyticsBot/1.0 (https://github.com/<kartsarav>; contact: <kartsarav@gmail.com>)"
wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent=USER_AGENT
)

# Step 2 — Load the page
page_title = "List of Marvel Cinematic Universe films"
page = wiki.page(page_title)

if not page.exists():
    raise Exception(f"The page '{page_title}' was not found on Wikipedia.")

print(f"✅ Successfully accessed page: {page.title}")

# Step 3 — Get the rendered HTML version (this contains the tables)
render_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}?action=render"
response = requests.get(render_url, headers={"User-Agent": USER_AGENT})

if response.status_code != 200:
    raise Exception(f"Failed to fetch render HTML (status {response.status_code})")

# Step 4 — Extract tables from HTML using pandas
tables = pd.read_html(response.text)
print(f"✅ Found {len(tables)} tables on the page.")

# Step 5 — Identify the main MCU films table
movie_tables = [
    t for t in tables
    if any(
        (isinstance(col, str) and col.lower() in ["film", "u.s. release date"]) or
        (isinstance(col, tuple) and any(isinstance(c, str) and c.lower() in ["film", "u.s. release date"] for c in col))
        for col in t.columns
    )
]

# Combine all the movie-related tables
if movie_tables:
    all_movies = pd.concat(movie_tables, ignore_index=True)
else:
    print("❌ No movie tables found.")
    exit()

# Save the combined CSV
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
output_path = os.path.join(root_dir, "data", "output", "csv", "marvel_movies.csv")
all_movies.to_csv(output_path, index=False)


print(f"✅ Successfully saved all Marvel movie tables to: {output_path}")