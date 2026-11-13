import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/NBK/NBK_2024_Annual_Report.pdf")

if not pdf_path.exists():
    raise SystemExit(f"PDF not found: {pdf_path}")

keywords = [
    "consolidated statement of financial position",
    "consolidated statement of income",
    "consolidated income statement",
    "consolidated statement of profit or loss"
]

with pdfplumber.open(pdf_path) as pdf:
    print("PDF:", pdf_path.name)
    print("Total pages:", len(pdf.pages))

    matches = []

    for index, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        normalised = " ".join(text.lower().split())

        found = [k for k in keywords if k in normalised]

        if found:
            matches.append((index + 1, found))

    print("\n========== MATCHING PAGES ==========")

    for page_number, found in matches:
        print(f"\nPDF PAGE: {page_number}")
        print("MATCHES:", ", ".join(found))

    print("\nTotal matching pages:", len(matches))
