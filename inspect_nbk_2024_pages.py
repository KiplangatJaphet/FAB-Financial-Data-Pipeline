import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/NBK/NBK_2024_Annual_Report.pdf")

with pdfplumber.open(pdf_path) as pdf:
    for page_number in range(128, 136):
        print("\n" + "=" * 75)
        print(f"PDF PAGE: {page_number}")
        print("=" * 75)

        text = pdf.pages[page_number - 1].extract_text(
            layout=False
        ) or ""

        print(text[:9000])
