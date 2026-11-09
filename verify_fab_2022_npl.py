
import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/FAB/FAB_2022_Annual_Report.pdf")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[9]

    print("=" * 80)
    print("FAB 2022 ANNUAL REPORT")
    print("PDF PAGE: 10")
    print("=" * 80)

    print("\nSTANDARD TEXT EXTRACTION")
    print("-" * 80)
    print(page.extract_text() or "No text found")

    print("\nLAYOUT-PRESERVING EXTRACTION")
    print("-" * 80)
    print(
        page.extract_text(
            layout=True,
            x_tolerance=2,
            y_tolerance=3
        ) or "No text found"
    )

print("\nINSPECTION COMPLETED")
