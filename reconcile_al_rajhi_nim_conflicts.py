import pandas as pd
import re
from pathlib import Path

ROOT = Path("output")
VERIFY = ROOT / "verification" / "Al_Rajhi_NIM"

SOURCE = VERIFY / "Al_Rajhi_NIM_year_assignment_audit.csv"
if not SOURCE.exists():
    SOURCE = ROOT / SOURCE.name

if not SOURCE.exists():
    raise SystemExit(f"Missing source file: {SOURCE}")

df = pd.read_csv(SOURCE).fillna("")

def parse_number(value):
    s = str(value).strip().replace(",", "")
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        number = float(s)
        return -number if negative else number
    except ValueError:
        return None

def raw_numbers(value):
    return [
        parse_number(x)
        for x in str(value).split("|")
        if parse_number(x) is not None
    ]

records = []
excluded = []

for _, row in df.iterrows():
    numbers = raw_numbers(row["Raw_Values"])
    report_year = int(row["Report_Year"])
    category = str(row["Category"])
    line = str(row["Raw_Line"])

    # Retain only simple two-column rows at this stage.
    if len(numbers) != 2:
        excluded.append({
            "Report_Year": report_year,
            "Category": category,
            "PDF_File": row["PDF_File"],
            "PDF_Page": row["PDF_Page"],
            "Raw_Line": line,
            "Reason": "COMPLEX_OR_MULTI_VALUE_ROW"
        })
        continue

    # Avoid mixing aggregate balances with breakdowns.
    if category in ("Impairment", "Structured_Products"):
        excluded.append({
            "Report_Year": report_year,
            "Category": category,
            "PDF_File": row["PDF_File"],
            "PDF_Page": row["PDF_Page"],
            "Raw_Line": line,
            "Reason": "REQUIRES_ACCOUNTING_CLASSIFICATION"
        })
        continue

    for position, (year, amount) in enumerate([
        (report_year, numbers[0]),
        (report_year - 1, numbers[1])
    ], start=1):

        if not 2009 <= year <= 2024:
            continue

        records.append({
            "Financial_Year": year,
            "Report_Year": report_year,
            "Column_Position": position,
            "Category": category,
            "Amount_SAR_Million_Candidate": amount / 1000,
            "PDF_File": row["PDF_File"],
            "PDF_Page": row["PDF_Page"],
            "Raw_Line": line,
            "Review_Flags": row["Review_Flags"],
            "Status": "CANDIDATE_NOT_VERIFIED"
        })

candidate = pd.DataFrame(records)

if candidate.empty:
    raise SystemExit("No two-column candidates found.")

# Compare distinct candidate values for each year/category.
# This is a screening exercise, not final financial verification.
summary = (
    candidate.groupby(["Financial_Year", "Category"])
    .agg(
        Candidate_Rows=("Amount_SAR_Million_Candidate", "size"),
        Distinct_Amounts=(
            "Amount_SAR_Million_Candidate",
            lambda x: len(set(x.round(3)))
        ),
        Minimum_Amount=("Amount_SAR_Million_Candidate", "min"),
        Maximum_Amount=("Amount_SAR_Million_Candidate", "max"),
        Source_Reports=("Report_Year", "nunique")
    )
    .reset_index()
)

summary["Review_Status"] = summary.apply(
    lambda r:
        "MULTIPLE_VALUES_REVIEW"
        if r["Distinct_Amounts"] > 1
        else "SINGLE_VALUE_CHECK_CLASSIFICATION",
    axis=1
)

# More targeted comparison: same category and normalised
# financial-statement line across different reports.
candidate["Normalised_Line"] = (
    candidate["Raw_Line"]
    .str.lower()
    .str.replace(r"\(?-?\d[\d,]*\)?", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

comparison = (
    candidate.groupby(
        ["Financial_Year", "Category", "Normalised_Line"]
    )
    .agg(
        Source_Reports=("Report_Year", "nunique"),
        Distinct_Amounts=(
            "Amount_SAR_Million_Candidate",
            lambda x: len(set(x.round(3)))
        ),
        Minimum_Amount=("Amount_SAR_Million_Candidate", "min"),
        Maximum_Amount=("Amount_SAR_Million_Candidate", "max")
    )
    .reset_index()
)

comparison = comparison[
    (comparison["Source_Reports"] > 1) &
    (comparison["Distinct_Amounts"] > 1)
].copy()

comparison["Difference_SAR_Million"] = (
    comparison["Maximum_Amount"] -
    comparison["Minimum_Amount"]
)

VERIFY.mkdir(parents=True, exist_ok=True)

candidate.to_csv(
    VERIFY / "Al_Rajhi_NIM_two_column_review.csv",
    index=False, encoding="utf-8-sig"
)

summary.to_csv(
    VERIFY / "Al_Rajhi_NIM_component_conflict_summary.csv",
    index=False, encoding="utf-8-sig"
)

comparison.to_csv(
    VERIFY / "Al_Rajhi_NIM_cross_report_conflicts.csv",
    index=False, encoding="utf-8-sig"
)

pd.DataFrame(
    excluded,
    columns=[
        "Report_Year", "Category", "PDF_File",
        "PDF_Page", "Raw_Line", "Reason"
    ]
).to_csv(
    VERIFY / "Al_Rajhi_NIM_complex_rows_review.csv",
    index=False, encoding="utf-8-sig"
)

print("=" * 65)
print("AL RAJHI - BATCH FINANCIAL CONFLICT SCREENING")
print("=" * 65)
print("Original candidate rows:", len(df))
print("Two-column year-assigned records:", len(candidate))
print("Complex/excluded candidate rows:", len(excluded))
print("Year-category groups:", len(summary))
print("Groups with multiple values:",
      (summary["Distinct_Amounts"] > 1).sum())
print("Cross-report line conflicts:", len(comparison))
print()
print("OUTPUT DIRECTORY:", VERIFY)
print("Main financial CSV: NOT MODIFIED")
print("Earning-assets matrix: NOT MODIFIED")
print("=" * 65)
