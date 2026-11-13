import pdfplumber
from pathlib import Path

PDF_DIR = Path("pdfs/NBK")
YEARS = range(2019, 2023)

KEYWORDS = [
    "consolidated statement of income",
    "consolidated statement of financial position",
]

print("\n========== NBK BATCH 2: 2019-2022 ==========")

for year in YEARS:
    path = PDF_DIR / f"NBK_{year}_Annual_Report.pdf"

    print(f"\n{'=' * 65}")
    print(f"YEAR: {year}")
    print(f"FILE: {path.name}")

    if not path.exists():
        print("STATUS: PDF MISSING")
        continue

    with pdfplumber.open(path) as pdf:
        print("TOTAL PAGES:", len(pdf.pages))

        candidates = []

        for index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = text.splitlines()
            heading = " ".join(lines[:5]).lower()

            matches = [
                keyword for keyword in KEYWORDS
                if keyword in heading
            ]

            if matches:
                candidates.append(index + 1)

        print("CANDIDATE PAGES:", candidates)

        for page_number in candidates:
            text = pdf.pages[page_number - 1].extract_text() or ""

            print(f"\n--- PDF PAGE {page_number} ---")
            print(text[:6500])

print("\n========== INSPECTION FINISHED ==========")
