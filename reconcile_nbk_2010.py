from pathlib import Path
import pandas as pd

dataset = Path("output/NBK_raw_financial_data.csv")
report = Path("output/NBK_2010_reconciliation.csv")

if report.exists():
    raise SystemExit("STOP: Reconciliation report already exists.")

df = pd.read_csv(dataset, low_memory=False)

rows = df.loc[df["Year"] == 2010]

if len(rows) != 1:
    raise SystemExit("STOP: Expected exactly one 2010 row.")

row = rows.iloc[0]

# Rounded historical actuals from Global Research,
# 22 February 2011, PDF pages 3 and 4.
verified = {
    "Shareholders_Equity_LCU_Millions": (2074.0, 4),
    "Profit_Before_Taxation_LCU_Millions": (320.0, 4),
    "Operating_Expenses_LCU_Millions": (159.0, 4),
    "Net_Interest_Income_LCU_Millions": (359.0, 4),
    "Gross_Loans_LCU_Millions": (8133.0, 4),
    "Non_Performing_Loans_LCU_Millions": (134.0, 4),
    "Published_CAR_Pct": (18.3, 3),
    "CIR_Pct": (31.9, 4),
    "NPL_Ratio_Pct": (1.6, 4),
}

records = []

for field, (proposed, page) in verified.items():
    if field not in df.columns:
        raise SystemExit(f"STOP: Missing column {field}")

    existing = pd.to_numeric(
        pd.Series([row[field]]),
        errors="coerce"
    ).iloc[0]

    if pd.isna(existing):
        status = "FILL_MISSING"
    elif abs(float(existing) - proposed) < 0.001:
        status = "MATCH"
    else:
        status = "CONFLICT_REVIEW"

    records.append({
        "Year": 2010,
        "Field": field,
        "Existing_Value": existing,
        "Proposed_Value": proposed,
        "Status": status,
        "Source_Document": "NBK_2010_Global_Research.pdf",
        "Source_PDF_Page": page,
        "Source_Type": "Third-party research",
        "Precision": "Rounded published figure",
    })

result = pd.DataFrame(records)
result.to_csv(report, index=False)

print("\n========== NBK 2010 RECONCILIATION ==========")
print(result.groupby("Status").size().to_string())
print("\nReport:", report)
print("Main dataset: UNCHANGED")
print("============================================")
