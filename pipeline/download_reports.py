
import argparse
import csv
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber
import requests


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
OUTPUT_DIR = ROOT / "output"
MANIFEST = ROOT / "pipeline" / "report_manifest.csv"
LOG_FILE = OUTPUT_DIR / "report_download_log.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AcademicResearchDownloader/1.0)",
    "Accept": "application/pdf,application/octet-stream,*/*",
}

LOG_FIELDS = [
    "timestamp_utc",
    "bank",
    "year",
    "filename",
    "status",
    "source_url",
    "details",
]


def verify_pdf(path):
    """Check the PDF signature and whether pages can be opened."""
    with open(path, "rb") as file:
        if file.read(5) != b"%PDF-":
            return False, "File does not start with a PDF signature"

    try:
        with pdfplumber.open(path) as pdf:
            count = len(pdf.pages)
            if count == 0:
                return False, "PDF contains no pages"
            return True, f"Valid PDF ({count} pages)"
    except Exception as error:
        return False, f"Unreadable PDF: {error}"


def download_pdf(url, destination):
    """Stream a PDF into a temporary file and verify before saving."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "manual_required", "No valid HTTP(S) source URL"

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None

    try:
        with requests.get(
            url,
            headers=HEADERS,
            timeout=(15, 90),
            stream=True,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower():
                return "manual_required", "Server returned an HTML page"

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".pdf",
                prefix="report_",
                dir=destination.parent,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        temp_file.write(chunk)

        valid, details = verify_pdf(temp_path)
        if not valid:
            return "manual_required", details

        # Never overwrite an existing file.
        if destination.exists():
            return "skipped_existing", "Destination already exists"

        # Exclusive creation protects against accidental replacement.
        with open(temp_path, "rb") as source:
            with open(destination, "xb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)

        return "downloaded", details

    except FileExistsError:
        return "skipped_existing", "Destination already exists"
    except requests.RequestException as error:
        return "manual_required", str(error)
    except (OSError, ValueError) as error:
        return "error", str(error)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def ensure_manifest():
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    if MANIFEST.exists():
        return

    with open(MANIFEST, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["bank", "year", "filename", "source_url"],
        )
        writer.writeheader()

        # QNB 2010 is already collected.
        # Additional verified official URLs will be added here.


def append_log(record):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exists = LOG_FILE.exists()

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_FIELDS)

        if not exists:
            writer.writeheader()

        writer.writerow(record)


def process_reports(bank_filter=None):
    ensure_manifest()

    with open(MANIFEST, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        reports = list(reader)

    if not reports:
        print(f"No reports configured in: {MANIFEST}")
        print("Add bank, year, filename and verified source_url entries.")
        return

    for report in reports:
        bank = (report.get("bank") or "").strip()
        year = (report.get("year") or "").strip()
        filename = (report.get("filename") or "").strip()
        url = (report.get("source_url") or "").strip()

        if bank_filter and bank.upper() != bank_filter.upper():
            continue

        if (
            not bank
            or not year.isdigit()
            or not 2010 <= int(year) <= 2024
            or not filename.lower().endswith(".pdf")
            or Path(filename).name != filename
            or not bank.replace("_", "").replace("-", "").isalnum()
        ):
            print(f"Skipping invalid manifest row: {report}")
            continue

        destination = PDF_DIR / bank / filename

        if destination.exists():
            valid, details = verify_pdf(destination)
            if valid:
                status = "skipped_existing"
            else:
                status = "manual_required"
                details = f"Existing file needs inspection: {details}"
        else:
            status, details = download_pdf(url, destination)

        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bank": bank,
            "year": year,
            "filename": filename,
            "status": status,
            "source_url": url,
            "details": details,
        }
        append_log(record)
        print(f"[{status}] {bank} {year}: {details}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and verify bank annual reports."
    )
    parser.add_argument(
        "--bank",
        help="Optional bank filter, for example QNB",
    )
    args = parser.parse_args()
    process_reports(args.bank)
