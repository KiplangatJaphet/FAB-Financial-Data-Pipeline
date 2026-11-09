
import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/FAB/FAB_2023_Annual_Report.pdf")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[98]  # PDF page 99

    print("=" * 75)
    print("FAB 2023 ANNUAL REPORT - PDF PAGE 99")
    print("=" * 75)

    # Full page, without truncating the text
    print(page.extract_text(layout=False))
