
import argparse
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


# ============================================================
# 1. FILE CONFIGURATION
# ============================================================

CSV_PATH = Path("output/FAB_raw_financial_data.csv")
BACKUP_DIR = Path("output/backups")

BANK_NAME = "First Abu Dhabi Bank"
YEAR = 2018
EXPECTED_COLUMNS = 58


# ============================================================
# 2. BUILD THE FAB 2018 RECORD
# ============================================================

def build_2018_record(columns):
    """
    Build FAB's 2018 record using original audited
    consolidated financial statements.

    All monetary amounts are in AED millions.
    """

    record = {column: None for column in columns}

    values = {
        "Bank_Name": BANK_NAME,
        "Country": "United Arab Emirates",
        "Year": YEAR,

        # ----------------------------------------------------
        # AUDITED FINANCIAL STATEMENTS
        # PDF pages 22-23
        # ----------------------------------------------------

        "Total_Assets_LCU_Millions": 744125.195,
        "Total_Liabilities_LCU_Millions": 642152.195,
        "Total_Equity_LCU_Millions": 101973.000,
        "Shareholders_Equity_LCU_Millions": 101611.278,

        "Net_Profit_LCU_Millions": 12066.389,
        "Profit_Before_Taxation_LCU_Millions": 12391.393,

        "Total_Operating_Income_LCU_Millions": 19445.742,
        "Operating_Expenses_LCU_Millions": 5328.555,
        "Net_Interest_Income_LCU_Millions": 13025.959,
        "Net_Impairment_Charge_LCU_Millions": 1725.794,

        "Loans_Advances_Islamic_Financing_LCU_Millions": 353205.228,

        "Customer_Accounts_Other_Deposits_LCU_Millions": 465475.874,

        # ----------------------------------------------------
        # GROSS LOANS
        # Note 12, PDF page 103
        # ----------------------------------------------------

        "Gross_Loans_LCU_Millions": 367056.491,

        # ----------------------------------------------------
        # NON-PERFORMING LOANS
        # Financial Performance, PDF page 1
        # ----------------------------------------------------

        # Published NPL balance is approximately AED 11.5bn.
        # Leave absolute NPL amount blank because it is rounded.

        "Non_Performing_Loans_LCU_Millions": None,
        "NPL_Ratio_Pct": 3.1,

        # ----------------------------------------------------
        # STAGE 3 CREDIT EXPOSURE
        # Note 5, PDF page 67
        # ----------------------------------------------------

        "Stage_3_Gross_Exposure_LCU_Millions": 8894.605,
        "Stage_3_Impairment_Allowance_LCU_Millions": 4682.146,

        # ----------------------------------------------------
        # REGULATORY CAPITAL
        # Audited Financial Statements, PDF page 92
        # ----------------------------------------------------

        "Total_Regulatory_Capital_LCU_Millions": 77394.707,
        "Eligible_Tier_1_Capital_LCU_Millions": 71692.908,
        "Additional_Tier_1_Capital_LCU_Millions": 10754.750,
        "Tier_2_Capital_LCU_Millions": 5701.799,

        # ----------------------------------------------------
        # RISK-WEIGHTED ASSETS
        # Audited Financial Statements, PDF page 92
        # ----------------------------------------------------

        "Credit_Risk_RWA_LCU_Millions": 427201.365,
        "Market_Risk_RWA_LCU_Millions": 29475.312,
        "Operational_Risk_RWA_LCU_Millions": 35696.011,
        "RWA_LCU_Millions": 492372.688,

        "Published_CAR_Pct": 15.7,

        # ----------------------------------------------------
        # REPORTING INFORMATION
        # ----------------------------------------------------

        "Reporting_Currency": "AED",
        "Reporting_Unit": "Millions",

        # ----------------------------------------------------
        # SOURCE DOCUMENTS
        # ----------------------------------------------------

        "Source_Document": (
            "FAB_2018_Financial_Statements.pdf; "
            "FAB_2018_Financial_Performance.pdf; "
            "FAB_2018_Pillar_3_Report.pdf.pdf"
        ),

        "Source_PDF_Page": "Financial Statements: 22-23",
        "Source_Printed_Pages": "Financial Statements: 11-12",

        "Gross_Loans_Source_PDF_Page": "103",

        "NPL_Source_PDF_Page": "Financial Performance: 1",

        "Stage_3_Source_PDF_Pages": "67",

        "CAR_Source_PDF_Page": (
            "Financial Statements: 92; "
            "Pillar 3: 11-12"
        ),

        # ----------------------------------------------------
        # ENTITY BASIS AND DATA QUALITY NOTES
        # ----------------------------------------------------

        "Entity_Basis_Note": (
            "FAB consolidated group, post NBAD-FGB merger. "
            "Financial figures are sourced from the original "
            "audited 2018 consolidated financial statements, "
            "not the pro forma merger-adjusted statements "
            "on PDF pages 4-5. "

            "Gross loans are sourced from Note 12, "
            "PDF page 103. "

            "Stage 3 gross exposure and impairment allowance "
            "are sourced from Note 5, PDF page 67. "
            "POCI exposure is separately disclosed and "
            "excluded from Stage 3 figures. "

            "The published NPL ratio is 3.1%. "
            "The published absolute NPL balance is "
            "approximately AED 11.5 billion and is rounded; "
            "therefore the absolute NPL field is blank. "

            "Regulatory capital and risk-weighted assets "
            "are sourced from the audited financial statements, "
            "PDF page 92, and cross-checked against the "
            "2018 Pillar 3 report. "

            "Original audited 2018 total assets are "
            "AED 744125.195 million. "
            "The 2019 audited comparative reports "
            "AED 743886.387 million for 2018, "
            "a difference of AED 238.808 million. "
            "Original audited 2018 figures are retained. "

            "The published 2018 net interest margin "
            "was not independently verified in the "
            "available 2018 documents. "

            "CIR is calculated using reported operating "
            "expenses divided by reported operating income, "
            "including integration-related expenses."
        ),

        # ----------------------------------------------------
        # 2017 OPENING BALANCES
        # From 2018 audited comparative figures
        # PDF page 22
        # ----------------------------------------------------

        "Previous_Year_Total_Assets_LCU_Millions": 668968.295,

        "Previous_Year_Total_Equity_LCU_Millions": 102209.413,

        "Previous_Year_Shareholders_Equity_LCU_Millions": 101722.398,

        # ----------------------------------------------------
        # PROFIT ATTRIBUTABLE TO SHAREHOLDERS
        # ----------------------------------------------------

        "Profit_Attributable_To_Shareholders_LCU_Millions": 12010.820,

        # ----------------------------------------------------
        # PROFITABILITY METADATA
        # ----------------------------------------------------

        "Opening_Balance_Source": (
            "FAB_2018_Financial_Statements.pdf"
        ),

        "Opening_Balance_Source_PDF_Page": "22",

        "ROA_Method": (
            "Net profit / average total assets * 100"
        ),

        "ROE_Method": (
            "Profit attributable to shareholders / "
            "average shareholders equity * 100"
        ),

        # ----------------------------------------------------
        # NET INTEREST MARGIN
        # No independently verified published figure
        # ----------------------------------------------------

        "NIM_Pct": None,
        "NIM_Source_Document": None,
        "NIM_Source_PDF_Page": None,
        "NIM_Method": None,
    }

    unknown_columns = set(values) - set(columns)

    if unknown_columns:
        raise ValueError(
            f"Unexpected column names: {sorted(unknown_columns)}"
        )

    record.update(values)

    # --------------------------------------------------------
    # CALCULATE AVERAGE BALANCES
    # --------------------------------------------------------

    record["Average_Total_Assets_LCU_Millions"] = (
        record["Total_Assets_LCU_Millions"]
        + record["Previous_Year_Total_Assets_LCU_Millions"]
    ) / 2

    record["Average_Total_Equity_LCU_Millions"] = (
        record["Total_Equity_LCU_Millions"]
        + record["Previous_Year_Total_Equity_LCU_Millions"]
    ) / 2

    record["Average_Shareholders_Equity_LCU_Millions"] = (
        record["Shareholders_Equity_LCU_Millions"]
        + record["Previous_Year_Shareholders_Equity_LCU_Millions"]
    ) / 2

    # --------------------------------------------------------
    # CALCULATE ROA
    # --------------------------------------------------------

    record["ROA_Pct"] = round(
        (
            record["Net_Profit_LCU_Millions"]
            / record["Average_Total_Assets_LCU_Millions"]
        ) * 100,
        2,
    )

    # --------------------------------------------------------
    # CALCULATE ROE
    # --------------------------------------------------------

    record["ROE_Pct"] = round(
        (
            record["Profit_Attributable_To_Shareholders_LCU_Millions"]
            / record["Average_Shareholders_Equity_LCU_Millions"]
        ) * 100,
        2,
    )

    # --------------------------------------------------------
    # CALCULATE COST-TO-INCOME RATIO
    # Correct expected value: 27.40%
    # --------------------------------------------------------

    record["CIR_Pct"] = round(
        (
            record["Operating_Expenses_LCU_Millions"]
            / record["Total_Operating_Income_LCU_Millions"]
        ) * 100,
        2,
    )

    # --------------------------------------------------------
    # CALCULATE CAPITAL ADEQUACY RATIO
    # --------------------------------------------------------

    record["CAR_Pct"] = round(
        (
            record["Total_Regulatory_Capital_LCU_Millions"]
            / record["RWA_LCU_Millions"]
        ) * 100,
        2,
    )

    return record


# ============================================================
# 3. VALIDATE FINANCIAL DATA
# ============================================================

def validate_record(record):
    """
    Validate the 2018 financial figures before insertion.
    """

    def close(actual, expected, tolerance=0.002):
        return abs(actual - expected) <= tolerance

    print("\nVALIDATING FAB 2018 FINANCIAL DATA")
    print("=" * 65)

    # --------------------------------------------------------
    # BALANCE SHEET
    # --------------------------------------------------------

    assets = record["Total_Assets_LCU_Millions"]

    liabilities_and_equity = (
        record["Total_Liabilities_LCU_Millions"]
        + record["Total_Equity_LCU_Millions"]
    )

    if not close(assets, liabilities_and_equity):
        raise ValueError("Balance sheet reconciliation failed.")

    print("PASS: Balance sheet reconciliation")

    # --------------------------------------------------------
    # GROSS LOANS TO NET LOANS
    # --------------------------------------------------------

    gross_loans = record["Gross_Loans_LCU_Millions"]

    interest_suspended = 1968.015
    expected_credit_loss = 11883.248

    calculated_net_loans = (
        gross_loans
        - interest_suspended
        - expected_credit_loss
    )

    reported_net_loans = (
        record["Loans_Advances_Islamic_Financing_LCU_Millions"]
    )

    if not close(calculated_net_loans, reported_net_loans):
        raise ValueError("Loan reconciliation failed.")

    print("PASS: Gross-to-net loan reconciliation")

    # --------------------------------------------------------
    # REGULATORY CAPITAL
    # --------------------------------------------------------

    calculated_capital = (
        record["Eligible_Tier_1_Capital_LCU_Millions"]
        + record["Tier_2_Capital_LCU_Millions"]
    )

    reported_capital = (
        record["Total_Regulatory_Capital_LCU_Millions"]
    )

    if not close(calculated_capital, reported_capital):
        raise ValueError("Regulatory capital reconciliation failed.")

    print("PASS: Regulatory capital reconciliation")

    # --------------------------------------------------------
    # RISK-WEIGHTED ASSETS
    # --------------------------------------------------------

    calculated_rwa = (
        record["Credit_Risk_RWA_LCU_Millions"]
        + record["Market_Risk_RWA_LCU_Millions"]
        + record["Operational_Risk_RWA_LCU_Millions"]
    )

    if not close(
        calculated_rwa,
        record["RWA_LCU_Millions"],
    ):
        raise ValueError("RWA reconciliation failed.")

    print("PASS: Risk-weighted assets reconciliation")

    # --------------------------------------------------------
    # PROFITABILITY RATIOS
    # --------------------------------------------------------

    expected_ratios = {
        "ROA_Pct": 1.71,
        "ROE_Pct": 11.81,
        "CIR_Pct": 27.40,
        "CAR_Pct": 15.72,
    }

    for field, expected in expected_ratios.items():
        actual = record[field]

        if not close(actual, expected, 0.005):
            raise ValueError(
                f"{field} validation failed: "
                f"expected {expected}, got {actual}"
            )

        print(f"PASS: {field} = {actual:.2f}%")

    # --------------------------------------------------------
    # MISSING DATA VALIDATION
    # --------------------------------------------------------

    if record["Non_Performing_Loans_LCU_Millions"] is not None:
        raise ValueError(
            "2018 absolute NPL balance must remain blank."
        )

    if record["NIM_Pct"] is not None:
        raise ValueError(
            "2018 NIM must remain blank until verified."
        )

    print("PASS: Missing NPL and NIM values handled correctly")

    print("\nALL 2018 VALIDATION CHECKS PASSED")


# ============================================================
# 4. MAIN EXECUTION
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate and optionally insert "
            "FAB 2018 financial data."
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Create a backup and insert the validated "
            "2018 record into the CSV."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # READ EXISTING CSV
    # --------------------------------------------------------

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    print("\nEXISTING DATASET")
    print("=" * 65)
    print("File:", CSV_PATH)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    if len(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Expected {EXPECTED_COLUMNS} columns, "
            f"found {len(df.columns)}."
        )

    if df.columns.duplicated().any():
        raise ValueError("Duplicate CSV columns detected.")

    if df.duplicated(
        subset=["Bank_Name", "Year"]
    ).any():
        raise ValueError(
            "Duplicate bank-year records detected."
        )

    # --------------------------------------------------------
    # PREVENT DUPLICATE 2018 INSERTION
    # --------------------------------------------------------

    already_exists = (
        (df["Bank_Name"] == BANK_NAME)
        & (df["Year"] == YEAR)
    ).any()

    if already_exists:
        raise ValueError(
            "FAB 2018 already exists in the CSV. "
            "No changes made."
        )

    # --------------------------------------------------------
    # BUILD AND VALIDATE 2018 RECORD
    # --------------------------------------------------------

    record = build_2018_record(df.columns)

    validate_record(record)

    # --------------------------------------------------------
    # PREPARE UPDATED DATASET
    # --------------------------------------------------------

    new_row = pd.DataFrame(
        [record],
        columns=df.columns,
    )

    result = pd.concat(
        [df, new_row],
        ignore_index=True,
    )

    result = result.sort_values(
        ["Bank_Name", "Year"]
    ).reset_index(drop=True)

    if len(result) != len(df) + 1:
        raise ValueError(
            "Unexpected number of records after insertion."
        )

    if list(result.columns) != list(df.columns):
        raise ValueError(
            "Column structure changed unexpectedly."
        )

    if result.duplicated(
        subset=["Bank_Name", "Year"]
    ).any():
        raise ValueError(
            "Duplicate bank-year records after insertion."
        )

    # --------------------------------------------------------
    # DISPLAY PREVIEW
    # --------------------------------------------------------

    print("\nFAB 2018 RECORD PREVIEW")
    print("=" * 65)

    for column in df.columns:
        print(f"{column}: {record[column]}")

    print("\nPROPOSED DATASET")
    print("=" * 65)

    print("Original rows:", len(df))
    print("Proposed rows:", len(result))
    print("Columns:", len(result.columns))

    print("\nYears:")
    print(result["Year"].tolist())

    # --------------------------------------------------------
    # DRY RUN
    # --------------------------------------------------------

    if not args.write:
        print("\n" + "=" * 65)
        print("DRY RUN SUCCESSFUL")
        print("Existing CSV has NOT been modified.")
        print("=" * 65)
        return

    # --------------------------------------------------------
    # CREATE BACKUP BEFORE WRITING
    # --------------------------------------------------------

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup_path = (
        BACKUP_DIR
        / f"FAB_before_2018_insertion_{timestamp}.csv"
    )

    shutil.copy2(
        CSV_PATH,
        backup_path,
    )

    print("\nBACKUP CREATED")
    print(backup_path)

    # --------------------------------------------------------
    # WRITE TO TEMPORARY FILE
    # --------------------------------------------------------

    temp_path = CSV_PATH.with_name(
        CSV_PATH.stem + "_2018_temp.csv"
    )

    try:

        result.to_csv(
            temp_path,
            index=False,
        )

        # ----------------------------------------------------
        # VALIDATE TEMPORARY CSV
        # ----------------------------------------------------

        check = pd.read_csv(temp_path)

        if len(check) != len(df) + 1:
            raise ValueError(
                "Temporary CSV row-count check failed."
            )

        if list(check.columns) != list(df.columns):
            raise ValueError(
                "Temporary CSV column check failed."
            )

        if check.duplicated(
            subset=["Bank_Name", "Year"]
        ).any():
            raise ValueError(
                "Duplicate records in temporary CSV."
            )

        # ----------------------------------------------------
        # VERIFY EXISTING RECORDS ARE PRESERVED
        # ----------------------------------------------------

        original = df.sort_values(
            ["Bank_Name", "Year"]
        ).reset_index(drop=True)

        preserved = check.loc[
            ~(
                (check["Bank_Name"] == BANK_NAME)
                & (check["Year"] == YEAR)
            )
        ].sort_values(
            ["Bank_Name", "Year"]
        ).reset_index(drop=True)

        pd.testing.assert_frame_equal(
            original,
            preserved,
            check_dtype=False,
            check_exact=False,
            rtol=1e-10,
            atol=1e-8,
        )

        print(
            "PASS: Existing 2019-2024 records "
            "preserved."
        )

        # ----------------------------------------------------
        # REPLACE CSV ONLY AFTER ALL CHECKS PASS
        # ----------------------------------------------------

        temp_path.replace(CSV_PATH)

    finally:

        if temp_path.exists():
            temp_path.unlink()

    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("FAB 2018 INSERTION SUCCESSFUL")
    print("=" * 65)

    print("CSV:", CSV_PATH)
    print("Total records:", len(result))
    print("Columns:", len(result.columns))
    print("Backup:", backup_path)


# ============================================================
# 5. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
