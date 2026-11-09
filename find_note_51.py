from pathlib import Path
import pdfplumber

pdf_path = next(
    Path("pdfs").rglob("FAB_2024_Annual_Report.pdf")
)

search_terms = [
    "comparative",
    "reclassification",
    "reclassified",
    "restated",
    "restatement",
    "prior period"
]

with pdfplumber.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        text_lower = text.lower()

        if any(term in text_lower for term in search_terms):
            print(f"\n{'=' * 70}")
            print(f"PDF PAGE: {page_number}")
            print("=" * 70)
            print(text[:6000])