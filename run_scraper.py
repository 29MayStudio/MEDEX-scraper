import os
import re
import sys
import json
import time
import zipfile
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("medex_scraper")

BASE_URL = "https://plus.medex.com.bd"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Directories and output files
HTML_DIR = "downloaded_pages"
LINKS_FILE = "brand_links.txt"
JSON_OUT = "medex_data.json"
ZIP_OUT = "medex_html_pages.zip"

def fetch_url(session, url, retries=5, backoff=2):
    """Fetches a URL with retries and exponential backoff."""
    for i in range(retries):
        try:
            response = session.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning(f"404 Not Found: {url}")
                return None
            logger.warning(f"Non-200 status {response.status_code} for {url}. Retrying ({i+1}/{retries})...")
            time.sleep(backoff * (i + 1))
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}. Retrying ({i+1}/{retries})...")
            time.sleep(backoff * (i + 1))
    return None

def extract_links_from_index(session, page_num, herbal=False):
    """Extracts all brand medicine links from a single index page."""
    if herbal:
        url = f"{BASE_URL}/brands?herbal=1&page={page_num}"
    else:
        url = f"{BASE_URL}/brands?page={page_num}"

    html = fetch_url(session, url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links = []
    # Brand cards usually have class 'brand-card' or link to /brands/
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Match pattern: https://plus.medex.com.bd/brands/123/name
        if "/brands/" in href and re.search(r"/brands/\d+/", href):
            # Ensure it's absolute
            if not href.startswith("http"):
                href = BASE_URL + href
            links.append(href)

    return list(set(links))

def gather_all_links(test_mode=False):
    """Gathers all brand links from normal and herbal index pages."""
    if os.path.exists(LINKS_FILE):
        logger.info(f"Loading existing links from {LINKS_FILE}")
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(links)} brand links.")
        return links

    logger.info("Starting extraction of brand links from index pages...")
    all_links = set()

    # 1. Normal/Allopathic brands: 1 to 844
    normal_pages = range(1, 845)
    if test_mode:
        normal_pages = range(1, 3) # page 1 and 2 for test
        logger.info("TEST MODE: Limiting normal pages to 1 and 2")

    # 2. Herbal brands: 1 to 31
    herbal_pages = range(1, 32)
    if test_mode:
        herbal_pages = range(1, 2) # page 1 for test
        logger.info("TEST MODE: Limiting herbal pages to 1")

    session = requests.Session()

    # We fetch concurrently to speed up index link extraction
    logger.info("Extracting normal brand links...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(extract_links_from_index, session, page, False): page for page in normal_pages}
        for future in as_completed(futures):
            p = futures[future]
            try:
                res = future.result()
                all_links.update(res)
                logger.info(f"Processed normal page {p}/{max(normal_pages)}: Found {len(res)} links.")
            except Exception as e:
                logger.error(f"Error on normal page {p}: {e}")

    logger.info("Extracting herbal brand links...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(extract_links_from_index, session, page, True): page for page in herbal_pages}
        for future in as_completed(futures):
            p = futures[future]
            try:
                res = future.result()
                all_links.update(res)
                logger.info(f"Processed herbal page {p}/{max(herbal_pages)}: Found {len(res)} links.")
            except Exception as e:
                logger.error(f"Error on herbal page {p}: {e}")

    links_list = sorted(list(all_links))
    logger.info(f"Finished index extraction. Found {len(links_list)} total unique brand links.")

    # Save links
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        for link in links_list:
            f.write(link + "\n")
    logger.info(f"Saved brand links to {LINKS_FILE}")
    return links_list

def download_brand_page(session, url, idx, total):
    """Downloads a single brand page and saves its HTML to disk."""
    # Extract brand ID
    match = re.search(r"/brands/(\d+)/", url)
    if not match:
        logger.warning(f"Could not extract brand ID from {url}")
        return False

    brand_id = match.group(1)
    file_path = os.path.join(HTML_DIR, f"{brand_id}.html")

    if os.path.exists(file_path):
        # Already downloaded
        return True

    html = fetch_url(session, url)
    if html:
        # Save HTML
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False

def download_all_pages(links, test_mode=False):
    """Downloads all HTML pages concurrently with progress reporting."""
    os.makedirs(HTML_DIR, exist_ok=True)

    if test_mode:
        links = links[:10]  # download 10 pages for test
        logger.info(f"TEST MODE: Limiting medicine downloads to {len(links)} pages")

    total_urls = len(links)
    logger.info(f"Starting download of {total_urls} brand pages...")

    session = requests.Session()

    # Use ThreadPoolExecutor for concurrent I/O
    completed = 0
    skipped = 0

    # Count already existing pages
    for url in links:
        match = re.search(r"/brands/(\d+)/", url)
        if match:
            brand_id = match.group(1)
            file_path = os.path.join(HTML_DIR, f"{brand_id}.html")
            if os.path.exists(file_path):
                skipped += 1

    completed = skipped
    logger.info(f"Resuming download: {skipped} pages already downloaded.")

    start_time = time.time()

    # We run with max_workers=40 for speed and safety
    with ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(download_brand_page, session, url, i, total_urls): url for i, url in enumerate(links)}

        for future in as_completed(futures):
            url = futures[future]
            try:
                success = future.result()
                if success:
                    # If it was actually downloaded now (not skipped previously)
                    # we can update completed
                    pass
            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")

            completed += 1
            if completed % 100 == 0 or completed == total_urls:
                elapsed = time.time() - start_time
                speed = (completed - skipped) / elapsed if elapsed > 0 else 0
                eta = (total_urls - completed) / speed if speed > 0 else 0
                logger.info(f"Progress: {completed}/{total_urls} ({completed/total_urls*100:.2f}%) | "
                            f"Speed: {speed:.2f} pages/sec | "
                            f"ETA: {eta/60:.2f} min")

    logger.info("Finished brand page downloading.")

def parse_html_file(file_path):
    """Parses a saved HTML brand file and extracts all structured elements."""
    filename = os.path.basename(file_path)
    brand_id_str = filename.replace(".html", "")
    try:
        brand_id = int(brand_id_str)
    except ValueError:
        brand_id = None

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    data = {
        "brand_id": brand_id,
        "brand_name": "",
        "dosage_form": "",
        "strength": "",
        "type": "allopathic",
        "slug": "",
        "generic_name": "",
        "generic_id": None,
        "generic_link": "",
        "manufacturer_name": "",
        "manufacturer_id": None,
        "manufacturer_link": "",
        "pack_image_url": "",
        "packages": [],
        "sections": {}
    }

    # 1. Brand name & dosage form
    h1 = soup.find("h1", class_="page-heading-1-l")
    if h1:
        # Extract brand name text (without dosage_form text)
        small_tag = h1.find("small")
        if small_tag:
            data["dosage_form"] = small_tag.get_text().strip()
            # remove small tag from h1 text
            small_tag.extract()
        data["brand_name"] = h1.get_text().strip()

        # Check herbal/allopathic type by looking for herbal badge or image
        # Standard scraper checked h1.page-heading-1-l img alt attribute
        img_badge = h1.find("img")
        if img_badge:
            alt = img_badge.get("alt", "")
            if "herbal" in alt.lower():
                data["type"] = "herbal"

    # 2. Slug
    # Can derive from name or just standard slug representation
    # Let's derive a slug representation: brand_name + dosage_form + strength

    # 3. Generic details
    generic_div = soup.find("div", attrs={"title": "Generic Name"})
    if generic_div:
        a_tag = generic_div.find("a")
        if a_tag:
            data["generic_name"] = a_tag.get_text().strip()
            href = a_tag.get("href", "")
            data["generic_link"] = href
            match = re.search(r"/generics/(\d+)", href)
            if match:
                data["generic_id"] = int(match.group(1))
        else:
            data["generic_name"] = generic_div.get_text().strip()

    # 4. Strength details
    strength_div = soup.find("div", attrs={"title": "Strength"})
    if strength_div:
        data["strength"] = strength_div.get_text().strip()

    # 5. Manufacturer details
    man_div = soup.find("div", attrs={"title": "Manufactured by"})
    if man_div:
        a_tag = man_div.find("a")
        if a_tag:
            data["manufacturer_name"] = a_tag.get_text().strip()
            href = a_tag.get("href", "")
            data["manufacturer_link"] = href
            match = re.search(r"/companies/(\d+)", href)
            if match:
                data["manufacturer_id"] = int(match.group(1))
        else:
            data["manufacturer_name"] = man_div.get_text().strip()

    # 6. Slug generation
    brand_combined = f"{data['brand_name']} {data['dosage_form']} {data['strength']}".strip()
    # Normalize slug
    slug = brand_combined.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    data["slug"] = slug

    # 7. Pack Image URL
    pack_img_btn = soup.find("a", class_=lambda x: x and ("pi-badge" in x or "innovator-brand-badge" in x))
    if pack_img_btn and pack_img_btn.get("href"):
        data["pack_image_url"] = pack_img_btn["href"]

    # 8. Packages & Prices
    for pkg in soup.find_all(class_="package-container"):
        pkg_data = {}
        pkg_data["raw_text"] = pkg.get_text(separator=" ", strip=True)

        unit_price_span = pkg.find(string=re.compile("Unit Price", re.IGNORECASE))
        if unit_price_span:
            val_span = unit_price_span.find_next("span")
            if val_span:
                pkg_data["unit_price"] = val_span.get_text().strip()

        strip_price_span = pkg.find(string=re.compile("Strip Price", re.IGNORECASE))
        if strip_price_span:
            val_span = strip_price_span.find_next("span")
            if val_span:
                pkg_data["strip_price"] = val_span.get_text().strip()

        pack_size = pkg.find(class_="pack-size-info")
        if pack_size:
            pkg_data["pack_size_info"] = pack_size.get_text().strip()

        data["packages"].append(pkg_data)

    # 9. Dynamic Accordion Sections (No data missing!)
    # Every section is characterized by class='ac-body'
    ac_bodies = soup.find_all(class_="ac-body")
    for body in ac_bodies:
        # Determine the header text and the section key (usually ID)
        sib = body.find_previous_sibling()
        section_id = None
        header_text = None

        if sib:
            section_id = sib.get("id")
            header_elem = sib.find(class_="ac-header")
            if header_elem:
                header_text = header_elem.get_text().strip()

        if not section_id:
            # Search parent elements to find ID
            curr = body
            while curr and not section_id:
                curr = curr.parent
                if curr:
                    section_id = curr.get("id")

        if not header_text and section_id:
            # Humanize section_id as a fallback for header_text
            header_text = section_id.replace("_", " ").title()
        elif not header_text:
            header_text = "Unknown Section"

        # Clean text and raw HTML content
        body_text = body.get_text().strip()
        body_html = str(body)

        # Save dynamically under 'sections'
        # This guarantees that if only one page has a thing, it is saved!
        data["sections"][header_text] = {
            "section_id": section_id,
            "text": body_text,
            "html": body_html
        }

    return data

def process_html_and_generate_json(test_mode=False):
    """Processes all saved HTML files and compiles them into a single JSON file."""
    logger.info("Processing saved HTML files to generate the structured JSON dataset...")

    files = [os.path.join(HTML_DIR, f) for f in os.listdir(HTML_DIR) if f.endswith(".html")]
    if test_mode:
        files = files[:10]
        logger.info(f"TEST MODE: Limiting HTML processing to {len(files)} files")

    total_files = len(files)
    logger.info(f"Found {total_files} HTML files to parse.")

    all_data = []

    # We can use ThreadPool for CPU/parsing concurrency as BeautifulSoup in parallel is very fast
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(parse_html_file, f): f for f in files}
        for future in as_completed(futures):
            f_path = futures[future]
            try:
                parsed_data = future.result()
                all_data.append(parsed_data)
            except Exception as e:
                logger.error(f"Error parsing file {f_path}: {e}")

            completed += 1
            if completed % 1000 == 0 or completed == total_files:
                elapsed = time.time() - start_time
                speed = completed / elapsed if elapsed > 0 else 0
                logger.info(f"Parsed {completed}/{total_files} files ({completed/total_files*100:.2f}%) | "
                            f"Speed: {speed:.2f} files/sec")

    # Sort the list of brand data by brand_id for clean and structured output
    all_data.sort(key=lambda x: x["brand_id"] if x["brand_id"] is not None else 999999)

    logger.info(f"Writing parsed data to {JSON_OUT}...")
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Successfully generated {JSON_OUT} containing {len(all_data)} medicine brand objects.")

def zip_html_files():
    """Zips the downloaded HTML files into a single zip archive."""
    logger.info(f"Zipping HTML files to {ZIP_OUT}...")
    start_time = time.time()

    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk directory
        for root, dirs, files in os.walk(HTML_DIR):
            for file in files:
                if file.endswith(".html"):
                    file_path = os.path.join(root, file)
                    # Archive path should be inside a folder in the zip
                    arcname = os.path.join("downloaded_pages", file)
                    zipf.write(file_path, arcname)

    elapsed = time.time() - start_time
    logger.info(f"Successfully created zip archive {ZIP_OUT} in {elapsed:.2f} seconds.")

def main():
    parser = argparse.ArgumentParser(description="Medex plus website scraper and JSON compiler")
    parser.add_argument("--test", action="store_true", help="Run in test mode with limited pages and brands")
    parser.add_argument("--skip-download", action="store_true", help="Skip crawling and downloading, parse local HTML files directly")
    args = parser.parse_args()

    global_start = time.time()

    if args.test:
        logger.info("=" * 60)
        logger.info("RUNNING SCRAPER IN TEST MODE (subset of pages/brands)")
        logger.info("=" * 60)

    if not args.skip_download:
        # Phase 1: Extract links
        links = gather_all_links(test_mode=args.test)

        # Phase 2: Download pages
        download_all_pages(links, test_mode=args.test)
    else:
        logger.info("Skipping download phase. Proceeding directly to parsing local HTML files.")

    # Phase 3: Parse and generate JSON
    process_html_and_generate_json(test_mode=args.test)

    # Phase 4: Zip downloaded HTML files
    zip_html_files()

    total_elapsed = time.time() - global_start
    logger.info(f"All operations completed in {total_elapsed/60:.2f} minutes.")

if __name__ == "__main__":
    main()
