from pathlib import Path
import pandas as pd

source = Path("output/NBK_raw_financial_data.csv")
destination = Path("output/NBK_2012_2014_reconciliation.csv")

if destination.exists():
    raise SystemExit(
        f"STOP: {destination} already exists. "
        "Existing reconciliation file preserved."
    )

df = pd.read_csv(source, low_memory=False)
df["Year"] = pd.to_numeric(df["Year"], errors="raise").astype(int)

# All values are KWD millions.
# 2012 uses restated comparatives from the 2013 statements.
verified = {
    2012: {
        "Total_Assets_LCU_Millions": 16492.471,
        "Total_Liabilities_LCU_Millions": 13876.476,
        "Total_Equity_LCU_Millions": 2615.995,
        "Shareholders_Equity_LCU_Millions": 2426.515,
        "Net_Profit_LCU_Millions": 308.597,
        "Profit_Attributable_To_Shareholders_LCU_Millions": 305.125,
        "Profit_Before_Taxation_LCU_Millions": 327.229,
        "Total_Operating_Income_LCU_Millions": 649.930,
        "Operating_Expenses_LCU_Millions": 183.683,
        "Net_Interest_Income_LCU_Millions": 397.824,
        "Net_Impairment_Charge_LCU_Millions": 139.018,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 9860.620,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 9507.754,
    },
    2013: {
        "Total_Assets_LCU_Millions": 18600.145,
        "Total_Liabilities_LCU_Millions": 15888.351,
        "Total_Equity_LCU_Millions": 2711.794,
        "Shareholders_Equity_LCU_Millions": 2508.844,
        "Net_Profit_LCU_Millions": 251.522,
        "Profit_Attributable_To_Shareholders_LCU_Millions": 238.137,
        "Profit_Before_Taxation_LCU_Millions": 270.408,
        "Total_Operating_Income_LCU_Millions": 626.250,
        "Operating_Expenses_LCU_Millions": 207.096,
        "Net_Interest_Income_LCU_Millions": 451.474,
        "Net_Impairment_Charge_LCU_Millions": 148.746,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 10695.317,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 10478.048,
    },
    2014: {
        "Total_Assets_LCU_Millions": 21784.131,
        "Total_Liabilities_LCU_Millions": 18913.591,
        "Total_Equity_LCU_Millions": 2870.540,
        "Shareholders_Equity_LCU_Millions": 2653.271,
        "Net_Profit_LCU_Millions": 273.654,
        "Profit_Attributable_To_Shareholders_LCU_Millions": 261.810,
        "Profit_Before_Taxation_LCU_Millions": 299.260,
        "Total_Operating_Income_LCU_Millions": 661.046,
        "Operating_Expenses_LCU_Millions": 215.091,
        "Net_Interest_Income_LCU_Millions": 469.338,
        "Net_Impairment_Charge_LCU_Millions": 146.695,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 11908.708,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 11259.736,
    },
}

sources = {
    2012: ("NBK_2013_Financial_Statements.pdf", "3;5", "Restated 2012 financial position"),
    2013: ("NBK_2013_Financial_Statements.pdf", "3;5", "Current-year consolidated figures"),
    2014: ("NBK_2015_Annual_Report.pdf", "100;102", "2014 comparative consolidated figures"),
}

records = []

for year, fields in verified.items():
    rows = df.loc[df["Year"] == year]

    if len(rows) != 1:
        raise SystemExit(f"STOP: Expected one row for {year}.")

    row = rows.iloc[0]
    document, pages, note = sources[year]

    assets = fields["Total_Assets_LCU_Millions"]
    liabilities = fields["Total_Liabilities_LCU_Millions"]
    equity = fields["Total_Equity_LCU_Millions"]

    if abs(assets - liabilities - equity) > 0.001:
        raise SystemExit(f"STOP: Accounting identity failed for {year}.")

    for field, proposed in fields.items():
        if field not in df.columns:
            raise SystemExit(f"STOP: Missing dataset column {field}.")

        existing = pd.to_numeric(
            pd.Series([row[field]]), errors="coerce"
        ).iloc[0]

        if pd.isna(existing):
            status = "MISSING_FILL"
            difference = None
        else:
            difference = round(proposed - float(existing), 3)
            status = (
                "MATCH"
                if abs(difference) < 0.001
                else "CONFLICT_REVIEW"
            )

        records.append({
            "Year": year,
            "Field": field,
            "Existing_Value": existing,
            "Verified_Value": proposed,
            "Difference": difference,
            "Status": status,
            "Verified_Source": document,
            "Verified_PDF_Pages": pages,
            "Source_Note": note,
        })

result = pd.DataFrame(records)

result.to_csv(destination, index=False)

print("\n========== NBK RECONCILIATION ==========")
print(result.groupby(["Year", "Status"]).size().to_string())
print("\nTotal indicators reviewed:", len(result))
print("Conflicts:", (result["Status"] == "CONFLICT_REVIEW").sum())
print("Missing values:", (result["Status"] == "MISSING_FILL").sum())
print("Report:", destination)
print("Main NBK dataset: UNCHANGED")
print("========================================")
