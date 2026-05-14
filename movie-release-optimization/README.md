🎬 Movie Release Optimization

Part of the Marvel Analytics by KS series — this project uses data analytics to determine the most optimal release timing for Marvel movies to maximize theatrical viewership and box office performance.

⸻

🧩 Project Overview

The goal of this project is to analyze historical movie data — including release dates, competing releases, and performance metrics — to uncover patterns and timing strategies that impact box office outcomes.
By combining data from Marvel, Fox, and Sony superhero films with industry-wide releases, this analysis aims to identify the best window for future releases.

⸻

🧠 Problem Definition

Dependent variable:
🎟️ Total number of tickets sold / box office revenue (viewership performance)

Independent variables (Tier 1 & Tier 2):
	•	Release month and season
	•	Day of week and holiday proximity
	•	Genre and production company
	•	Competing major releases (±60 days window)
	•	IMDb and TMDB popularity metrics
	•	Budget and marketing proxy indicators
	•	Franchise continuity and studio ownership (Marvel, Fox, Sony)

## 🧩 Folder Structure
movie-release-optimization
* data
  * raw
  	* kaggle
    * scraped
  * processing
    * filter 1
    * filter 2
    * filter 3  
  * cleaned
  * output
* notebooks (Jupyter notebooks for analysis)
* scripts (Reusable Python or SQL scripts)
  * python 
  * visuals (Graphs, dashboards, and charts)
  * docs (Supporting notes or references)
  * README.md (You are here)
  * roadmap.md

⚙️ Tools & Technologies
Category
Tools Used
Languages
Python, SQL
Libraries
Pandas, NumPy, Matplotlib, Seaborn, OpenPyXL
Data Sources
Kaggle (IMDB & TMDB datasets), Wikipedia API
Visualization
Tableau, Excel
Version Control
Git & GitHub

🧮 Workflow Summary
	1.	Data Collection
	•	Gathered movie datasets from Kaggle (IMDB + TMDB).
	•	Scraped Marvel movie data (release dates, studios) from Wikipedia via Python.
	2.	Data Cleaning & Filtering
	•	Removed non-theatrical releases.
	•	Filtered competitors within ±60 days of each Marvel release.
	3.	Analysis
	•	Examined correlations between release timing, competition, and revenue.
	•	Visualized patterns using Python and Tableau.
	4.	Insights
	•	Identified seasonal and strategic patterns influencing performance.
	•	Built foundation for predictive modeling in future versions.

📊 Example Outputs
	•	filtered_movies.csv — list of competing movies around each Marvel release
	•	marvel_movies.csv — scraped Marvel movie release data from Wikipedia
	•	Visual dashboards exploring release timing vs. performance

📜 Data Credits
Source
Description
Kaggle Datasets
TMDB + IMDB merged data, including metadata and revenue
Wikipedia
Tables of Marvel Cinematic Universe and related studio releases
Manual Curation
Validation of post-acquisition Fox and Sony titles

Large raw datasets are not uploaded due to GitHub file size limits.
Refer to /data/raw/README.txt for download links.

🧭 Roadmap (Progress)
Phase
Status
🗂️ Setup
✅ Completed
📊 Data Cleaning
✅ In Progress
🧮 Analysis
⏳ Upcoming
📈 Visualization
⏳ Upcoming
🧾 Documentation
🏁 Final stage

💡 About the Author

Kartik Saravanan
Industrial & Systems Engineering @ University of Washington
Exploring data analytics, process optimization, and creative problem-solving through real-world projects.

📧 kartsarav@gmail.com
🔗 LinkedIn￼
