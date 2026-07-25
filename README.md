# bd-medicine-scraper

A remastered Django and Scrapy-based system to scrape medicine data from medex.com.bd and expose/export it.

## Overview
This codebase crawls pharmaceutical, brand, generic, dosage form, manufacturer, indication, and drug class details. The collected data is populated in a PostgreSQL (or SQLite) database, integrated with Django REST Framework, and can be exported as `.json` files.

## Features
- **Scrapy Spiders**: Crawls medicine, manufacturer, generic, drug class, dosage form, and indication data from `medex.com.bd`.
- **Django Integration**: Integrates Scrapy items directly with Django models using `scrapy-djangoitem`.
- **Django Admin Customization**: Autocomplete, alphabetical filtering, and custom bulk actions to **export selected records directly to JSON**.
- **JSON Export Command**: A management command to export any model data to structured JSON.
- **GitHub Actions Workflow**: Runs the scraper automatically on a 7-day schedule, generates `.json` release assets, and uploads them to the GitHub Release page automatically.

## Requirements & Setup

Create a Python virtual environment and install the dependencies:
```bash
pip install -r requirements.txt
```

Prepare database migrations and apply them:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Running the Crawler

To crawl all data sequentially:
```bash
python run_crawler.py
```

Or run a specific spider using Django commands:
```bash
python manage.py med_crawl
python manage.py manufacturer_crawl
python manage.py generic_crawl
python manage.py drug_class_crawl
python manage.py dosage_form_crawl
python manage.py indication_crawl
```

Mapping generics with medicines:
```bash
python manage.py med_generic_mapper
```

## Exporting to JSON

Export any crawled model to structured JSON using the management command:
```bash
python manage.py export_json <model_name> <export_path>
```
For example:
```bash
python manage.py export_json medicine medicine_data
```
This will output a formatted `medicine_data.json` file.

You can also use bulk actions in Django Admin to export records directly as JSON.

## Automated Scrapers (CI/CD)
The project includes a GitHub Actions workflow configured to run every 7 days (or manually via workflow dispatch). It runs the scraper, generates JSON files for all models, and automatically publishes them to a new GitHub Release.
