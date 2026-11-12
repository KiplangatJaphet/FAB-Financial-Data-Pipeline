
from pathlib import Path
import csv
import re
import pdfplumber

# Project directories
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs" / "Bank_Muscat"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "bank_muscat_pdf_validation.csv"

results = []

print("=" * 75)
print("BANK MUSCAT ANNUAL REPORT VALIDATION (2010–2024)")
print("=" * 75)

for year in range(2010, 2025):

    filename = f"Bank_Muscat_{year}_Annual_Report.pdf"
    pdf_path = PDF_DIR / filename

    result = {
        "bank": "Bank Muscat",
        "year": year,
        "filename": filename,
        "file_size_mb": 0,
        "total_pages": 0,
        "year_found": False,
        "financial_statements_found": False,
        "status": "",
        "error": ""
    }

    print(f"\nChecking {filename}")

    if not pdf_path.exists():
        result["status"] = "MISSING"
        print("  Status: MISSING")
        results.append(result)
        continue

    size = pdf_path.stat().st_size
    result["file_size_mb"] = round(size / (1024 * 1024), 2)

    if size == 0:
        result["status"] = "EMPTY"
        print("  Status: EMPTY")
        results.append(result)
        continue

    try:
        with pdfplumber.open(pdf_path) as pdf:

            total_pages = len(pdf.pages)
            result["total_pages"] = total_pages

            # Inspect selected pages throughout the PDF.
            # This is a screening check, not full verification.
            indices = set(range(min(10, total_pages)))

            if total_pages:
                indices.update({
                    total_pages // 4,
                    total_pages // 2,
                    (3 * total_pages) // 4,
                    total_pages - 1
                })

            text_parts = []

            for index in sorted(indices):
                page_text = pdf.pages[index].extract_text() or ""
                text_parts.append(page_text)

            text = "\n".join(text_parts).lower()

            # Look for the expected year as a standalone number.
            result["year_found"] = bool(
                re.search(rf"\b{year}\b", text)
            )

            financial_terms = [
                "financial statements",
                "statement of financial position",
                "balance sheet",
                "income statement",
                "statement of comprehensive income",
                "cash flows"
            ]

            result["financial_statements_found"] = any(
                term in text for term in financial_terms
            )

            if total_pages == 0:
                result["status"] = "REVIEW"
            elif (
                result["year_found"]
                and result["financial_statements_found"]
            ):
                result["status"] = "PASS_SCREENING"
            else:
                result["status"] = "REVIEW"

            print(f"  Size: {result['file_size_mb']} MB")
            print(f"  Pages: {total_pages}")
            print(f"  Expected year found: {result['year_found']}")
            print(
                "  Financial statements found: "
                f"{result['financial_statements_found']}"
            )
            print(f"  Status: {result['status']}")

    except Exception as error:
        result["status"] = "ERROR"
        result["error"] = str(error)
        print(f"  Error: {error}")

    results.append(result)


# Save validation results
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)


# Summary
print("\n" + "=" * 75)
print("VALIDATION SUMMARY")
print("=" * 75)

for status in [
    "PASS_SCREENING",
    "REVIEW",
    "MISSING",
    "EMPTY",
    "ERROR"
]:
    count = sum(
        1 for row in results if row["status"] == status
    )
    print(f"{status}: {count}")

print(f"\nValidation report saved to:\n{OUTPUT_FILE}")
