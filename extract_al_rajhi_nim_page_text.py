import pandas as pd
import pdfplumber
from pathlib import Path

PDF_DIR = Path("pdfs/Al_Rajhi")
OUT_DIR = Path("output")
SOURCE = OUT_DIR / "Al_Rajhi_NIM_detailed_candidates.csv"
DEST = OUT_DIR / "Al_Rajhi_NIM_verified_page_text.csv"

if not SOURCE.exists():
    raise SystemExit(f"Missing input: {SOURCE}")

df = pd.read_csv(SOURCE)

required = {"PDF_File", "PDF_Page", "Category"}
missing = required - set(df.columns)

if missing:
    raise SystemExit(f"Missing columns: {sorted(missing)}")

records = []
errors = []

print("=" * 65)
print("AL RAJHI - BATCH NIM SOURCE EXTRACTION")
print("=" * 65)

for filename, group in df.groupby("PDF_File", sort=True):

    pdf_path = PDF_DIR / filename

    if not pdf_path.exists():
        errors.append(f"Missing PDF: {filename}")
        continue

    pages = sorted(
        set(
            pd.to_numeric(
                group["PDF_Page"],
                errors="coerce"
            ).dropna().astype(int)
        )
    )

    print(f"\nProcessing: {filename}")
    print(f"Unique candidate pages: {len(pages)}", flush=True)

    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_number in pages:

                if not 1 <= page_number <= len(pdf.pages):
                    errors.append(
                        f"Invalid page {page_number}: {filename}"
                    )
                    continue

                page = pdf.pages[page_number - 1]
                text = page.extract_text() or ""

                matching = group[
                    pd.to_numeric(
                        group["PDF_Page"],
                        errors="coerce"
                    ) == page_number
                ]

                categories = sorted(
                    matching["Category"].dropna().unique()
                )

                records.append({
                    "PDF_File": filename,
                    "PDF_Page": page_number,
                    "Categories": " | ".join(categories),
                    "Candidate_Count": len(matching),
                    "Full_Page_Text": text,
                    "Text_Length": len(text)
                })

    except Exception as exc:
        errors.append(f"{filename}: {exc}")
        print(f"ERROR: {exc}")

columns = [
    "PDF_File",
    "PDF_Page",
    "Categories",
    "Candidate_Count",
    "Full_Page_Text",
    "Text_Length"
]

result = pd.DataFrame(records, columns=columns)

result.to_csv(
    DEST,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 65)
print("BATCH EXTRACTION COMPLETE")
print("=" * 65)
print("Candidate records:", len(df))
print("PDFs referenced:", df["PDF_File"].nunique())
print("Unique source pages extracted:", len(result))
print("Pages with no extracted text:",
      int((result["Text_Length"] == 0).sum()))
print("Errors:", len(errors))
print("Saved to:", DEST)
print("Main financial CSV: NOT MODIFIED")

for error in errors:
    print("WARNING:", error)
