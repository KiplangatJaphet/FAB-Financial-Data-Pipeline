
import pdfplumber
from pathlib import Path

reports = {
    2023: Path("pdfs/FAB/FAB_2023_Annual_Report.pdf"),
    2024: Path("pdfs/FAB/FAB_2024_Annual_Report.pdf"),
}

keywords = [
    "net interest margin",
    "nim",
    "interest earning assets",
    "interest-earning assets",
]

for year, pdf_path in reports.items():

    if not pdf_path.exists():
        print(f"Missing file: {pdf_path}")
        continue

    print("\n" + "=" * 75)
    print(f"FAB {year} ANNUAL REPORT")
    print("=" * 75)

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(
            pdf.pages, start=1
        ):

            text = page.extract_text() or ""
            lines = text.splitlines()

            matches = [
                i for i, line in enumerate(lines)
                if any(
                    keyword in line.lower()
                    for keyword in keywords
                )
            ]

            if not matches:
                continue

            print(f"\nPDF PAGE: {page_number}")

            for i in matches:
                start = max(0, i - 2)
                end = min(len(lines), i + 4)

                print("\n".join(lines[start:end]))
                print("-" * 50)
