# Medex Pharmaceutical Scraper to JSON

An automated Scrapy and Django-based system designed to crawl and scrape comprehensive medicine and pharmaceutical data from `medex.com.bd` and export the collected data into structured JSON files.

## Project Goal
The sole objective of this repository is to scrape `medex.com.bd` pharmaceutical data and export it into high-quality, formatted JSON assets. A GitHub Actions workflow automates this crawling and exporting cycle on a scheduled basis (every 7 days), publishing the newly updated `.json` files directly as GitHub Release assets.

## Scraped Models
- **Medicine**: Details on specific brands, strengths, pack sizes, packaging, dosage forms, generics, and manufacturers.
- **Generic**: Comprehensive information about active ingredients, indications, pharmacologies, dosage descriptions, side effects, and warning descriptions.
- **Manufacturer**: All pharmaceutical companies and brand names counts.
- **Dosage Form**: Diverse administration forms and respective counts.
- **Drug Class**: Drug classifications and list of generics.
- **Indication**: Clinical indications and mapping.

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

To run the complete scraping pipeline sequentially:
```bash
python run_crawler.py
```

This sequentially executes all the individual Scrapy crawlers (`manufacturer_crawl`, `generic_crawl`, `med_crawl`, `med_generic_mapper`, `drug_class_crawl`, `dosage_form_crawl`, and `indication_crawl`) to populate the database.

---

## Exporting Crawled Data to JSON

You can export any populated model to structured JSON using the Django management command:
```bash
python manage.py export_json <model_name> [outfile]
```

For example:
```bash
python manage.py export_json medicine medicine_data
```
This generates a formatted `medicine_data.json` file containing all crawled records.

---

## CI/CD Automation

This repository includes a scheduled GitHub Actions workflow (`.github/workflows/scrape_and_release.yml`) which runs automatically every Sunday (or can be triggered manually via workflow dispatch).

The workflow:
1. Sets up Python 3.11 and **Node.js 24**.
2. Installs dependencies and runs migrations.
3. Executes the full crawler suite (`python run_crawler.py`).
4. Exports all crawled data models to individual `.json` files.
5. Commits a new GitHub Release with the date as tag, uploading all `.json` data assets automatically.
