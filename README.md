# Medex Pharmaceutical Scraper to JSON

An automated Scrapy and Django-based scraper system designed to crawl and scrape comprehensive medicine and pharmaceutical data from `medex.com.bd` and export the collected data into structured JSON files.

## Project Goal
The sole objective of this repository is to scrape `medex.com.bd` pharmaceutical data and export it into high-quality, formatted JSON assets. A GitHub Actions workflow automates this crawling and exporting cycle on a scheduled basis (every 7 days), publishing the newly updated `.json` files directly as GitHub Release assets.

## Simplified Architecture
Instead of utilizing multiple separate crawlers for each data model, this system uses a single, highly integrated and robust **Medicine Crawler**.

1. **Integrated Crawling**: The crawler starts at the medicine brand listings on Medex. As it scrapes each brand, it:
   - Resolves and records medicine brand properties (name, type, dosage form, strength, package container, and pack size info).
   - Dynamically resolves and creates/saves the brand's **Manufacturer** if it doesn't already exist.
   - Dynamically detects if the brand's **Generic** monograph exists. If not, it requests and scrapes the detailed Generic page (indications, pharmacology, dosage, warnings, side effects, etc.).
2. **Relational Mapping**: A quick mapping command (`med_generic_mapper`) links medicines back to their newly scraped generics once the crawler finishes.
3. **Data Quality**: Safe DOM selectors and robust `sync_to_async` compatibility environments ensure zero crashes and complete data retention.

---

## Requirements & Setup

1. **Python Setup**: Ensure Python 3.11+ is installed.
2. **Node.js Setup**: Node.js 24 is used within the automated runner workflows to support modernized dependency chains and release integrations.
3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**:
   The crawler relies on Django's ORM to map, validate, and store scraped items. Prepare and apply the database migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

---

## Running the Scraper Locally

To run the unified scraping pipeline:
```bash
python run_crawler.py
```

This command sequentially runs the single `med_crawl` command to populate the database with medicines, manufacturers, and generics, then executes `med_generic_mapper` to connect them.

---

## Exporting Crawled Data to JSON

You can export the populated models to structured JSON using the Django management command:
```bash
python manage.py export_json <model_name> [outfile]
```

For example:
```bash
python manage.py export_json medicine medicine_data
python manage.py export_json generic generic_data
python manage.py export_json manufacturer manufacturer_data
```

This generates formatted `.json` files (e.g., `medicine_data.json`) containing all crawled records with clear relational keys. For detailed information on the JSON file schema and code examples on how to parse/query them in any language, see [JSON_STRUCTURE.md](JSON_STRUCTURE.md).

---

## CI/CD Automation

This repository includes a scheduled GitHub Actions workflow (`.github/workflows/scrape_and_release.yml`) which runs automatically every Sunday (or can be triggered manually via workflow dispatch).

The workflow:
1. Sets up Python 3.11 and **Node.js 24**.
2. Installs dependencies and runs migrations.
3. Executes the unified crawler pipeline (`python run_crawler.py`).
4. Exports all populated crawled data models (`medicine`, `generic`, and `manufacturer`) to individual `.json` files.
5. Commits a new GitHub Release with the date as tag, uploading all `.json` data assets automatically.
