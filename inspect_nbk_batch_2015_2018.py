import pdfplumber
from pathlib import Path

for year in range(2015, 2019):
    path = Path(f"pdfs/NBK/NBK_{year}_Annual_Report.pdf")

    print(f"\n========== NBK {year} ==========")

    if not path.exists():
        print("PDF MISSING:", path)
        continue

    with pdfplumber.open(path) as pdf:
        print("Total pages:", len(pdf.pages))

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = text.splitlines()
            heading = " ".join(lines[:7]).lower()

            if (
                "consolidated statement of income" in heading
                or "consolidated statement of financial position" in heading
            ):
                print(f"\nPDF PAGE {i + 1}")
                print(text[:1800])
