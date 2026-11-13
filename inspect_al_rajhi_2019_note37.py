import pdfplumber
from pathlib import Path

pdf = Path("pdfs/Al_Rajhi/Al_Rajhi_2019_Annual_Report.pdf")

if not pdf.exists():
    raise SystemExit(f"PDF not found: {pdf}")

with pdfplumber.open(pdf) as document:
    for index, page in enumerate(document.pages):
        text = page.extract_text() or ""
        lines = text.splitlines()

        for i, line in enumerate(lines):
            if (
                "37." in line
                and any(
                    word in line.lower()
                    for word in ["restat", "comparative", "reclass"]
                )
            ):
                print(f"\nPDF PAGE: {index + 1}")
                print("\n".join(lines[max(0, i-3):i+45]))
                break
