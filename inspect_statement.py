from pathlib import Path
import pdfplumber

pdf_path = next(
    Path("pdfs").rglob("FAB_2024_Annual_Report.pdf")
)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[110]

    midpoint = page.width / 2

    left_page = page.crop(
        (0, 0, midpoint, page.height)
    )

    right_page = page.crop(
        (midpoint, 0, page.width, page.height)
    )

    print("\nSTATEMENT OF FINANCIAL POSITION")
    print("=" * 60)
    print(left_page.extract_text())

    print("\nSTATEMENT OF PROFIT OR LOSS")
    print("=" * 60)
    print(right_page.extract_text())