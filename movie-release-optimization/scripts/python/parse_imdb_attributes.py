# date created: 11.26.2025
import pandas as pd
import os
import re

# === PATH SETTINGS ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

INPUT_FILE = os.path.join(root_dir, "data", "processing", "filter 2", "csv", "imdb_attributes_movies.csv")
OUTPUT_FILE = os.path.join(root_dir, "data", "output", "csv", "imdb_attributes_counts.csv")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# === REGEX FOR MATCHING LABEL COUNTS ===
pattern = re.compile(r"([a-zA-Z]+)\s*\((\d+)\)")

def parse_counts(attr_text):
    """
    Given a string like:
    'internet (20), blank (5), premiere (3)'
    return:
    blank_count, internet_count, total_count
    """
    blank_count = 0
    internet_count = 0
    total_count = 0

    if not isinstance(attr_text, str):
        return blank_count, internet_count, total_count

    matches = pattern.findall(attr_text)

    for label, count_str in matches:
        label = label.strip().lower()
        count = int(count_str)
        total_count += count

        if label == "blank":
            blank_count = count
        elif label == "internet":
            internet_count = count

    return blank_count, internet_count, total_count


# === LOAD INPUT CSV ===
print("🔹 Loading IMDb attribute CSV...")
df = pd.read_csv(INPUT_FILE)

# === PROCESS EACH ROW ===
blank_list = []
internet_list = []
total_list = []

print("🔎 Extracting blank & internet counts...")
for _, row in df.iterrows():
    attr_text = row.get("attributes", "")
    blank_count, internet_count, total_count = parse_counts(attr_text)

    blank_list.append(blank_count)
    internet_list.append(internet_count)
    total_list.append(total_count)

# === BUILD OUTPUT DATAFRAME ===
output_df = pd.DataFrame({
    "title": df["title"],
    "blank": blank_list,
    "internet": internet_list,
    "total": total_list
})

# === SAVE OUTPUT CSV ===
output_df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Done! Saved parsed counts to: {OUTPUT_FILE}")