import re
import pandas as pd
import pdfplumber
from pathlib import Path
from collections import Counter

BASE = Path("pdfs/Al_Rajhi")
OUT = Path("output")
INDEX = OUT / "Al_Rajhi_NIM_relevant_pages.csv"
RESULT = OUT / "Al_Rajhi_NIM_detailed_candidates.csv"

if not INDEX.exists():
    raise SystemExit("ERROR: Relevant-pages index not found.")

pages = pd.read_csv(INDEX)

PATTERNS = {
    "Net_Financing": r"^\s*financing\s*,?\s*net\b",
    "SAMA_Mutajara": r"^\s*mutajara\s+with\s+sama\b",
    "Interbank_Mutajara": r"^\s*mutajara\b",
    "Government_Murabaha": r"^\s*murabaha\s+with\s+(?:saudi\s+government|sama)\b",
    "Sukuk": r"^\s*sukuk\b",
    "Structured_Products": r"^\s*structured\s+products?\b",
    "Impairment": r"^\s*less:\s*(?:impairment|expected\s+credit\s+loss)",
}

NUMBER = re.compile(
    r"\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?"
    r"|\(?-?\d{4,}(?:\.\d+)?\)?"
)

YEAR = re.compile(r"\b(?:19|20)\d{2}\b")

records = []
errors = []

print("=" * 65)
print("AL RAJHI - BATCH DETAILED FINANCIAL EXTRACTION")
print("=" * 65)

for filename, group in pages.groupby("PDF_File", sort=True):
    path = BASE / filename
    print("\nProcessing:", filename, flush=True)

    if not path.exists():
        errors.append((filename, "PDF missing"))
        continue

    count = 0

    try:
        with pdfplumber.open(path) as pdf:
            for page_no in sorted(group["PDF_Page"].unique()):
                page_no = int(page_no)

                if not 1 <= page_no <= len(pdf.pages):
                    errors.append((filename, f"Invalid page {page_no}"))
                    continue

                text = pdf.pages[page_no - 1].extract_text() or ""
                lines = text.splitlines()

                for i, line in enumerate(lines):
                    category = None

                    for name, pattern in PATTERNS.items():
                        if re.search(pattern, line, re.I):
                            category = name
                            break

                    if category is None:
                        continue

                    values = NUMBER.findall(line)

                    if not values:
                        continue

                    context_before = " ".join(
                        lines[max(0, i - 5):i]
                    )
                    context_after = " ".join(
                        lines[i + 1:i + 3]
                    )

                    years = YEAR.findall(
                        context_before + " " + line
                    )

                    records.append({
                        "PDF_File": filename,
                        "PDF_Page": page_no,
                        "Category": category,
                        "Raw_Line": line.strip(),
                        "Raw_Values": " | ".join(values),
                        "Value_Count": len(values),
                        "Nearby_Years": " | ".join(
                            dict.fromkeys(years)
                        ),
                        "Context_Before": context_before[:500],
                        "Context_After": context_after[:250],
                        "Validation_Status": "UNVERIFIED",
                    })

                    count += 1

        print(" Detailed candidate rows:", count, flush=True)

    except Exception as exc:
        errors.append((filename, str(exc)))
        print(" ERROR:", exc, flush=True)

columns = [
    "PDF_File", "PDF_Page", "Category",
    "Raw_Line", "Raw_Values", "Value_Count",
    "Nearby_Years", "Context_Before",
    "Context_After", "Validation_Status"
]

df = pd.DataFrame(records, columns=columns)
df.to_csv(RESULT, index=False, encoding="utf-8-sig")

print("\n" + "=" * 65)
print("BATCH EXTRACTION COMPLETE")
print("=" * 65)
print("Detailed candidate records:", len(df))
print("Files with errors:", len(errors))

print("\nCATEGORY COUNTS:")
for category, count in sorted(
    Counter(df["Category"]).items()
):
    print(f" {category}: {count}")

print("\nRECORDS BY REPORT:")
if not df.empty:
    print(
        df.groupby("PDF_File")
        .size()
        .to_string()
    )

if errors:
    print("\nERRORS:")
    for filename, error in errors:
        print(filename, ":", error)

print("\nOutput:", RESULT)
print("All values remain unverified.")
print("Main financial CSV: NOT MODIFIED")
