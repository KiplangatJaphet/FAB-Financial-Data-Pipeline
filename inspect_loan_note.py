
from pathlib import Path
import pdfplumber

# Locate the FAB 2024 annual report
pdf_path = next(
    Path("pdfs").rglob("FAB_2024_Annual_Report.pdf")
)

# Terms that may identify the loan disclosures
search_terms = [
    "gross loans",
    "non-performing loans",
    "non performing loans",
    "loans and advances",
    "impairment allowance",
    "expected credit losses",
    "credit-impaired"
]

print(f"Inspecting: {pdf_path.name}")

with pdfplumber.open(pdf_path) as pdf:

    for page_number, page in enumerate(pdf.pages, start=1):

        page_text = page.extract_text() or ""
        text_lower = page_text.lower()

        matches = [
            term for term in search_terms
            if term in text_lower
        ]

        if matches:
            print("\n" + "=" * 75)
            print(f"PDF PAGE: {page_number}")
            print(f"KEYWORDS: {', '.join(matches)}")
            print("=" * 75)

            print(page_text[:5000])
