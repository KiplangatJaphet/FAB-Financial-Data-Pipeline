
from pathlib import Path
import pdfplumber

pdf_path = next(
    Path("pdfs").rglob("FAB_2024_Annual_Report.pdf")
)

search_terms = [
    "non-performing loans",
    "non performing loans",
    "stage 3",
    "credit quality",
    "impaired loans",
    "past due",
    "credit risk exposure",
    "gross carrying amount"
]

with pdfplumber.open(pdf_path) as pdf:

    for page_number, page in enumerate(pdf.pages, start=1):

        # Focus on the financial risk management section
        if not 160 <= page_number <= 180:
            continue

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

            print(page_text[:6000])
