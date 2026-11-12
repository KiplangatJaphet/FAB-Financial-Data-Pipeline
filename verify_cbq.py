from pathlib import Path
import pdfplumber

folder = Path("pdfs/CBQ")

for year in range(2010, 2025):
    file = folder / f"CBQ_{year}_Annual_Report.pdf"

    try:
        with pdfplumber.open(file) as pdf:
            text = " ".join(
                (page.extract_text() or "")
                for page in pdf.pages[:5]
            ).lower()

            bank_found = (
                "commercial bank" in text
                or "commercialbank" in text
            )

            print(
                f"{year} | Pages: {len(pdf.pages)} "
                f"| Bank identified: {bank_found}"
            )

    except Exception as e:
        print(f"{year} | ERROR: {e}")
