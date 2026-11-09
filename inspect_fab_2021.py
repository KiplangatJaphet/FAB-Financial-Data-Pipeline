
import pdfplumber
from pathlib import Path

reports = {
    "ANNUAL REPORT": {
        "path": Path("pdfs/FAB/FAB_2021_Annual_Report.pdf"),
        "pages": [7, 16, 17, 73],
    },
    "FINANCIAL STATEMENTS": {
        "path": Path("pdfs/FAB/FAB_2021_Financial_Statements.pdf"),
        "pages": [9, 10, 46, 60, 90, 91, 124],
    },
    "PILLAR 3 REPORT": {
        "path": Path("pdfs/FAB/FAB_2021_Pillar_3_Report.pdf"),
        "pages": [29],
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
                raise ValueError(
                    f"Invalid PDF page {page_number} "
                    f"for {pdf_path.name}"
                )

            page = pdf.pages[page_number - 1]
            extracted_text = page.extract_text() or ""

            print("\n" + "=" * 85)
            print(f"DOCUMENT: {report_name}")
            print(f"FILE: {pdf_path.name}")
            print(f"PDF PAGE: {page_number}")
            print("=" * 85)

            print(extracted_text)

print("\nEXTRACTION COMPLETED")
