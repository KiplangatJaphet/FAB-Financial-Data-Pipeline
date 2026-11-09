
import pdfplumber
from pathlib import Path

reports = {
    "ANNUAL REPORT": {
        "path": Path("pdfs/FAB/FAB_2022_Annual_Report.pdf"),
        "pages": [20, 82],
    },
    "FINANCIAL STATEMENTS": {
        "path": Path("pdfs/FAB/FAB_2022_Financial_Statements.pdf"),
        "pages": [9, 84, 116],
    },
    "PILLAR 3 REPORT": {
        "path": Path("pdfs/FAB/FAB_2022_Pillar_3_Report.pdf"),
        "pages": [30],
    },
}

for report_name, report in reports.items():

    pdf_path = report["path"]

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Missing PDF: {pdf_path}"
        )

    with pdfplumber.open(pdf_path) as pdf:

        for page_number in report["pages"]:

            if page_number > len(pdf.pages):
                print(
                    f"Invalid page {page_number} "
                    f"for {pdf_path.name}"
                )
                continue

            page = pdf.pages[page_number - 1]
            text = page.extract_text(layout=False) or ""

            print("\n" + "=" * 85)
            print(f"DOCUMENT: {report_name}")
            print(f"FILE: {pdf_path.name}")
            print(f"PDF PAGE: {page_number}")
            print("=" * 85)
            print(text)

print("\nEXTRACTION COMPLETED")
