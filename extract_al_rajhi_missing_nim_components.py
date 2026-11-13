import re
import pdfplumber
import pandas as pd
from pathlib import Path

PDF_DIR = Path("pdfs/Al_Rajhi")
OUT_DIR = Path("output/verification/Al_Rajhi_NIM")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MATRIX = OUT_DIR / "Al_Rajhi_NIM_provisional_earning_assets_matrix.csv"

if not MATRIX.exists():
    raise SystemExit(f"Missing provisional matrix: {MATRIX}")

matrix = pd.read_csv(MATRIX)

patterns = {
    "Sukuk_Amortised_Cost": [
        r"sukuk.*amorti[sz]ed cost",
        r"amorti[sz]ed cost.*sukuk"
    ],
    "Sukuk_FVSI": [
        r"sukuk.*fair value through income",
        r"sukuk.*fair value through profit",
        r"sukuk.*fvsi",
        r"sukuk.*fvtpl"
    ],
    "Sukuk_FVOCI": [
        r"sukuk.*fair value through other comprehensive",
        r"sukuk.*fvoci"
    ],
    "Sukuk_General": [
        r"\bsukuk\b",
        r"\binvestment securities\b"
    ],
    "SAMA_Mutajara": [
        r"mutajara.*sama",
        r"sama.*mutajara",
        r"placements.*sama"
    ],
    "Interbank_Mutajara": [
        r"interbank.*mutajara",
        r"mutajara.*banks",
        r"due from banks"
    ],
    "Government_Murabaha": [
        r"murabaha.*government",
        r"murabaha.*sama",
        r"government.*murabaha"
    ],
    "ECL_Review": [
        r"expected credit losses",
        r"impairment allowance",
        r"allowance for impairment",
        r"credit loss allowance"
    ]
}

compiled = {
    category: [re.compile(p, re.I) for p in expressions]
    for category, expressions in patterns.items()
}

def report_year(filename):
    match = re.search(r"20\d{2}", filename)
    return int(match.group()) if match else None

def numbers(text):
    return " | ".join(
        re.findall(
            r"(?<![A-Za-z])\(?-?\d[\d,]*(?:\.\d+)?\)?",
            text
        )
    )

def is_pending(year, category):
    if category == "Sukuk_General":
        return True

    rows = matrix[
        (matrix["Year"] == year) &
        (matrix["Component"] == category)
    ]

    if rows.empty:
        return True

    return rows["Verified_Amount_SAR_Million"].isna().all()

records = []
coverage = []
errors = []

pdf_files = sorted(PDF_DIR.glob("Al_Rajhi_*.pdf"))

if not pdf_files:
    raise SystemExit("No Al Rajhi PDFs found.")

for pdf_path in pdf_files:

    year = report_year(pdf_path.name)
    print(f"Processing: {pdf_path.name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:

            matched_pages = 0
            matched_lines = 0

            for page_index, page in enumerate(pdf.pages):

                text = page.extract_text() or ""
                if not text.strip():
                    continue

                lines = text.splitlines()
                page_has_match = False

                for line_index, line in enumerate(lines):

                    matched_categories = [
                        category
                        for category, expressions in compiled.items()
                        if any(p.search(line) for p in expressions)
                    ]

                    if not matched_categories:
                        continue

                    page_has_match = True
                    matched_lines += 1

                    before = " ".join(
                        lines[max(0, line_index - 2):line_index]
                    )

                    after = " ".join(
                        lines[line_index + 1:line_index + 4]
                    )

                    for category in matched_categories:

                        records.append({
                            "Report_Year": year,
                            "PDF_File": pdf_path.name,
                            "PDF_Page": page_index + 1,
                            "Category": category,
                            "Priority": (
                                "MISSING_COMPONENT"
                                if is_pending(year, category)
                                else "CROSSCHECK_EXISTING"
                            ),
                            "Source_Line": line,
                            "Numeric_Tokens": numbers(line),
                            "Context_Before": before,
                            "Context_After": after,
                            "Amount_SAR_Million": "",
                            "Financial_Year": "",
                            "Balance_Type": "",
                            "Unit_Confirmed": "",
                            "Verification_Status": "REQUIRES_REVIEW"
                        })

                if page_has_match:
                    matched_pages += 1

            coverage.append({
                "Report_Year": year,
                "PDF_File": pdf_path.name,
                "Total_Pages": len(pdf.pages),
                "Matched_Pages": matched_pages,
                "Matched_Lines": matched_lines
            })

    except Exception as exc:
        errors.append({
            "PDF_File": pdf_path.name,
            "Error": str(exc)
        })
        print(f"ERROR: {exc}")

columns = [
    "Report_Year", "PDF_File", "PDF_Page",
    "Category", "Priority", "Source_Line",
    "Numeric_Tokens", "Context_Before",
    "Context_After", "Amount_SAR_Million",
    "Financial_Year", "Balance_Type",
    "Unit_Confirmed", "Verification_Status"
]

details = pd.DataFrame(records, columns=columns)

details = details.drop_duplicates(
    subset=["PDF_File", "PDF_Page", "Category", "Source_Line"]
)

details = details.sort_values(
    ["Priority", "Report_Year", "Category", "PDF_Page"]
)

coverage_df = pd.DataFrame(coverage)

summary = (
    details.groupby(
        ["Report_Year", "Category", "Priority"],
        dropna=False
    )
    .agg(
        Candidate_Lines=("Source_Line", "size"),
        Source_Pages=("PDF_Page", "nunique")
    )
    .reset_index()
)

details_file = OUT_DIR / "Al_Rajhi_NIM_missing_components_candidates.csv"
summary_file = OUT_DIR / "Al_Rajhi_NIM_missing_components_summary.csv"
coverage_file = OUT_DIR / "Al_Rajhi_NIM_missing_components_pdf_coverage.csv"
errors_file = OUT_DIR / "Al_Rajhi_NIM_missing_components_errors.csv"

details.to_csv(details_file, index=False, encoding="utf-8-sig")
summary.to_csv(summary_file, index=False, encoding="utf-8-sig")
coverage_df.to_csv(coverage_file, index=False, encoding="utf-8-sig")
pd.DataFrame(errors, columns=["PDF_File", "Error"]).to_csv(
    errors_file, index=False, encoding="utf-8-sig"
)

print("\n" + "=" * 65)
print("AL RAJHI - MISSING EARNING-ASSET COMPONENTS")
print("=" * 65)
print("PDFs processed:", len(coverage))
print("Candidate records:", len(details))
print("Missing-component priority records:",
      (details["Priority"] == "MISSING_COMPONENT").sum())
print("Errors:", len(errors))
print()
print("FILES CREATED:")
print(details_file)
print(summary_file)
print(coverage_file)
print(errors_file)
print()
print("Candidate amounts: NOT YET VERIFIED")
print("Provisional matrix: NOT MODIFIED")
print("Main financial CSV: NOT MODIFIED")
print("=" * 65)
