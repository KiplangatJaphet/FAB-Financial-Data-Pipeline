
import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/FAB/FAB_2024_Annual_Report.pdf")

keywords = [
    "risk weighted assets",
    "risk-weighted assets",
    "capital adequacy ratio",
    "total capital",
    "regulatory capital",
    "capital adequacy"
]

with pdfplumber.open(pdf_path) as pdf:

    for page_number, page in enumerate(pdf.pages, start=1):

        text = page.extract_text() or ""
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in keywords):

            print("\n" + "=" * 80)
            print(f"PDF PAGE: {page_number}")
            print("=" * 80)
            print(text)
