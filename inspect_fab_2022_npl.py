
import pdfplumber
from pathlib import Path

pdf_path = Path(
    "pdfs/FAB/FAB_2022_Financial_Statements.pdf"
)

pages_to_inspect = [47, 48, 49, 83, 84, 85, 86]

with pdfplumber.open(pdf_path) as pdf:

    for page_number in pages_to_inspect:

        page = pdf.pages[page_number - 1]

        print("\n" + "=" * 80)
        print(f"PDF PAGE: {page_number}")
        print("=" * 80)

        print(page.extract_text(layout=False) or "")

print("\nINSPECTION COMPLETED")
