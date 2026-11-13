import pandas as pd
import re
from pathlib import Path

ROOT = Path("output")
VERIFY = ROOT / "verification" / "Al_Rajhi_NIM"
VERIFY.mkdir(parents=True, exist_ok=True)

CANDIDATES = ROOT / "Al_Rajhi_NIM_detailed_candidates.csv"
PAGES = ROOT / "Al_Rajhi_NIM_verified_page_text.csv"

DETAIL_OUT = VERIFY / "Al_Rajhi_NIM_classification_review.csv"
MATRIX_OUT = VERIFY / "Al_Rajhi_NIM_earning_assets_matrix.csv"
SUMMARY_OUT = VERIFY / "Al_Rajhi_NIM_classification_summary.csv"

if not CANDIDATES.exists():
    CANDIDATES = VERIFY / CANDIDATES.name

if not PAGES.exists():
    PAGES = VERIFY / PAGES.name

for path in (CANDIDATES, PAGES):
    if not path.exists():
        raise SystemExit(f"Missing input: {path}")

candidates = pd.read_csv(CANDIDATES).fillna("")
pages = pd.read_csv(PAGES).fillna("")

required = {
    "PDF_File", "PDF_Page", "Category",
    "Raw_Line", "Raw_Values"
}

missing = required - set(candidates.columns)

if missing:
    raise SystemExit(f"Missing columns: {sorted(missing)}")

page_lookup = {}

for _, row in pages.iterrows():
    key = (str(row["PDF_File"]), int(row["PDF_Page"]))
    page_lookup[key] = str(row["Full_Page_Text"])

def report_year(filename):
    match = re.search(r"20\d{2}", str(filename))
    return int(match.group()) if match else None

def parse_amounts(raw):
    values = []
    for token in str(raw).split("|"):
        token = token.strip().replace(",", "")
        negative = token.startswith("(") and token.endswith(")")
        token = token.strip("()")
        try:
            value = float(token)
            if negative:
                value = -value
            values.append(value)
        except ValueError:
            pass
    return values

categories = {
    "Net_Financing": "Net_Customer_Financing",
    "SAMA_Mutajara": "SAMA_Mutajara",
    "Interbank_Mutajara": "Interbank_Mutajara",
    "Government_Murabaha": "Government_Murabaha",
    "Sukuk": "Sukuk",
    "Structured_Products": "Structured_Products_Review",
    "Impairment": "ECL_Review"
}

records = []

for _, row in candidates.iterrows():

    filename = str(row["PDF_File"])
    page = int(row["PDF_Page"])
    year = report_year(filename)

    values = parse_amounts(row["Raw_Values"])

    source_text = page_lookup.get((filename, page), "")

    raw_line = str(row["Raw_Line"])
    category = str(row["Category"])

    amount_1 = values[0] if len(values) > 0 else None
    amount_2 = values[1] if len(values) > 1 else None

    # A report's first two columns may represent current and
    # comparative years, but this must be confirmed manually.
    if year and len(values) >= 2:
        proposed_years = f"{year} | {year - 1}"
    else:
        proposed_years = "REVIEW REQUIRED"

    records.append({
        "Report_Year": year,
        "PDF_File": filename,
        "PDF_Page": page,
        "Original_Category": category,
        "Proposed_Component": categories.get(
            category, "Other_Review"
        ),
        "Raw_Line": raw_line,
        "Raw_Values": str(row["Raw_Values"]),
        "Amount_1_Raw": amount_1,
        "Amount_2_Raw": amount_2,
        "Proposed_Column_Years": proposed_years,
        "Nearby_Years": str(row.get("Nearby_Years", "")),
        "Source_Page_Available": bool(source_text.strip()),
        "Context_Before": str(row.get("Context_Before", "")),
        "Context_After": str(row.get("Context_After", "")),
        "Verified_Year": "",
        "Verified_Amount_SAR_Million": "",
        "Verified_Component": "",
        "Unit_Confirmed": "",
        "Financial_Status": "REQUIRES_VERIFICATION"
    })

detail = pd.DataFrame(records)

detail.to_csv(
    DETAIL_OUT, index=False, encoding="utf-8-sig"
)

components = [
    "Net_Customer_Financing",
    "SAMA_Mutajara",
    "Interbank_Mutajara",
    "Government_Murabaha",
    "Sukuk_Amortised_Cost",
    "Sukuk_FVSI",
    "Sukuk_FVOCI",
    "Structured_Products_Review",
    "ECL_Review"
]

matrix = []

for year in range(2010, 2025):
    for component in components:
        matrix.append({
            "Year": year,
            "Component": component,
            "Verified_Amount_SAR_Million": "",
            "Source_PDF": "",
            "Source_Page": "",
            "Source_Reporting_Year": "",
            "Verification_Status": "PENDING",
            "Notes": ""
        })

matrix = pd.DataFrame(matrix)

matrix.to_csv(
    MATRIX_OUT, index=False, encoding="utf-8-sig"
)

summary = (
    detail.groupby(
        ["Report_Year", "Proposed_Component"],
        dropna=False
    )
    .agg(
        Candidate_Count=("Raw_Line", "size"),
        Pages=("PDF_Page", "nunique"),
        Source_Pages_Available=(
            "Source_Page_Available", "sum"
        )
    )
    .reset_index()
)

summary.to_csv(
    SUMMARY_OUT, index=False, encoding="utf-8-sig"
)

print("=" * 65)
print("AL RAJHI - BATCH NIM CLASSIFICATION")
print("=" * 65)
print("Candidates processed:", len(detail))
print("Research years:", 15)
print("Component-year rows:", len(matrix))
print("Source pages available:",
      detail["Source_Page_Available"].sum())
print("Missing source-page matches:",
      (~detail["Source_Page_Available"]).sum())
print()
print("FILES CREATED:")
print(DETAIL_OUT)
print(MATRIX_OUT)
print(SUMMARY_OUT)
print()
print("Financial amounts: NOT YET VERIFIED")
print("Main financial CSV: NOT MODIFIED")
print("=" * 65)
