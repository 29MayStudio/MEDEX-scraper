# Medex Pharmaceutical Scraper to JSON & HTML

An automated, modern, and high-performance Python scraper designed to download all medicine brand webpages from `plus.medex.com.bd` and export the collected data into a structured JSON file and zipped HTML files.

## Project Goal
The objective of this repository is to scrape `plus.medex.com.bd` pharmaceutical data, saving every individual brand page (25,000+ pages) in `.html` format, and parsing them into a single comprehensive `.json` file. A GitHub Actions workflow automates this crawling, exporting, and releasing cycle on manual trigger (`workflow_dispatch`), publishing the outputs directly as GitHub Release assets.

---

## Output Datasets
Each release publishes two main files:
1. **`medex_data.json`**: A structured, unified JSON dataset containing every medicine brand page's extracted elements (brand name, dosage form, strength, generic monograph, manufacturer, pricing, and all accordion monograph sections such as indications, pharmacology, dosage, interaction, side effects, etc.).
2. **`medex_html_pages.zip`**: A compressed zip archive of all downloaded individual `.html` files named by their unique `brand_id`.

---

## Requirements & Setup

1. **Python Setup**: Ensure Python 3.11+ is installed.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Scraper Locally

To run the scraper:
```bash
python run_scraper.py
```

### Script Modes:
- **Test Mode**: To run a quick End-to-End test of the index crawler, page downloader, and HTML parser on a small subset of pages (approx. 10 brands):
  ```bash
  python run_scraper.py --test
  ```
- **Skip Download**: If you already have HTML files in `downloaded_pages/` and want to parse them to regenerate the JSON file and ZIP without fetching from the web:
  ```bash
  python run_scraper.py --skip-download
  ```

---

## CI/CD Automation

This repository includes a GitHub Actions workflow (`.github/workflows/scrape_and_release.yml`) which runs on a manual trigger (`workflow_dispatch`).

The workflow:
1. Sets up Python 3.11.
2. Installs required lightweight dependencies.
3. Executes the scraper script (`python run_scraper.py`).
4. Generates `medex_data.json` and `medex_html_pages.zip`.
5. Publishes a new GitHub Release with the date as tag, uploading the assets automatically.
