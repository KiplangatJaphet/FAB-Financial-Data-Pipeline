
from pathlib import Path
from datetime import datetime
import argparse
import shutil

import pandas as pd


CSV_PATH = Path("output/FAB_raw_financial_data.csv")
BACKUP_DIR = Path("output/backups")

FINANCIAL_STATEMENTS = "FAB_2019_Financial_Statements.pdf"
ANNUAL_REVIEW = "FAB_2019_Annual_Review.pdf"
PILLAR_3 = "FAB_2019_Pillar_3_Report.pdf.pdf"

EXPECTED_COLUMNS = 58


def check_close(actual, expected, label, tolerance=0.001):
    if abs(actual - expected) > tolerance:
        raise ValueError(
            f"{label} failed: {actual} != {expected}"
        )


def build_2019_record():

    # All financial amounts are AED millions.
    # Original audited statements report AED thousands.

    assets_2019 = 821968.015
    assets_2018 = 743886.387

    liabilities_2019 = 713930.979

    equity_2019 = 108037.036
    equity_2018 = 101973.000

    shareholders_equity_2019 = 107606.562
    shareholders_equity_2018 = 101611.278

    net_profit = 12592.623
    shareholders_profit = 12520.203
    profit_before_tax = 12907.086

    operating_income = 20249.057
    operating_expenses = 5498.991
    net_interest_income = 12774.802
    impairment_charge = 1842.980

    gross_loans = 421730.328
    interest_suspended = 2799.157
    loan_ecl = 11028.143
    net_loans = 407903.028

    customer_deposits = 519161.857

    stage_3_exposure = 11768.567
    stage_3_allowance = 4581.173

    cet1_capital = 65615.547
    additional_tier_1 = 10754.750
    tier_1_capital = cet1_capital + additional_tier_1

    tier_2_capital = 5597.785
    regulatory_capital = 81968.082

    credit_rwa = 423419.312
    market_rwa = 25737.601
    operational_rwa = 35913.142
    total_rwa = 485070.055

    # Published ratios
    published_npl_ratio = 3.20
    published_car = 16.90
    published_nim = 2.11

    # Calculated ratios
    average_assets = (assets_2019 + assets_2018) / 2

    average_equity = (equity_2019 + equity_2018) / 2

    average_shareholders_equity = (
        shareholders_equity_2019 + shareholders_equity_2018
    ) / 2

    roa = round(net_profit / average_assets * 100, 2)

    roe = round(
        shareholders_profit / average_shareholders_equity * 100,
        2,
    )

    cir = round(operating_expenses / operating_income * 100, 2)

    car = round(regulatory_capital / total_rwa * 100, 2)

    # Financial validations
    check_close(
        liabilities_2019 + equity_2019,
        assets_2019,
        "Balance sheet",
    )

    check_close(
        gross_loans - interest_suspended - loan_ecl,
        net_loans,
        "Gross-to-net loans",
    )

    check_close(
        cet1_capital + additional_tier_1 + tier_2_capital,
        regulatory_capital,
        "Regulatory capital",
    )

    check_close(
        credit_rwa + market_rwa + operational_rwa,
        total_rwa,
        "Risk-weighted assets",
    )

    check_close(car, published_car, "Capital adequacy ratio", 0.01)

    check_close(roa, 1.61, "ROA", 0.01)
    check_close(roe, 11.97, "ROE", 0.01)
    check_close(cir, 27.16, "CIR", 0.01)

    record = {
        "Bank_Name": "First Abu Dhabi Bank",
        "Country": "United Arab Emirates",
        "Year": 2019,

        "Total_Assets_LCU_Millions": assets_2019,
        "Total_Liabilities_LCU_Millions": liabilities_2019,
        "Total_Equity_LCU_Millions": equity_2019,
        "Shareholders_Equity_LCU_Millions":
            shareholders_equity_2019,

        "Net_Profit_LCU_Millions": net_profit,
        "Profit_Before_Taxation_LCU_Millions":
            profit_before_tax,

        "Total_Operating_Income_LCU_Millions":
            operating_income,

        "Operating_Expenses_LCU_Millions":
            operating_expenses,

        "Net_Interest_Income_LCU_Millions":
            net_interest_income,

        "Net_Impairment_Charge_LCU_Millions":
            impairment_charge,

        "Loans_Advances_Islamic_Financing_LCU_Millions":
            net_loans,

        "Gross_Loans_LCU_Millions": gross_loans,

        "Customer_Accounts_Other_Deposits_LCU_Millions":
            customer_deposits,

        # Absolute published NPL amount not independently
        # established. Do not substitute Stage 3 exposure.
        "Non_Performing_Loans_LCU_Millions": None,

        "Stage_3_Gross_Exposure_LCU_Millions":
            stage_3_exposure,

        "Stage_3_Impairment_Allowance_LCU_Millions":
            stage_3_allowance,

        "Total_Regulatory_Capital_LCU_Millions":
            regulatory_capital,

        "Eligible_Tier_1_Capital_LCU_Millions":
            tier_1_capital,

        "Additional_Tier_1_Capital_LCU_Millions":
            additional_tier_1,

        "Tier_2_Capital_LCU_Millions":
            tier_2_capital,

        "Credit_Risk_RWA_LCU_Millions": credit_rwa,
        "Market_Risk_RWA_LCU_Millions": market_rwa,
        "Operational_Risk_RWA_LCU_Millions":
            operational_rwa,

        "RWA_LCU_Millions": total_rwa,

        "Published_CAR_Pct": published_car,

        "Reporting_Currency": "AED",
        "Reporting_Unit": "Millions",

        "Source_Document": (
            f"{FINANCIAL_STATEMENTS}; "
            f"{ANNUAL_REVIEW}; "
            f"{PILLAR_3}"
        ),

        "Source_PDF_Page": "Financial Statements: 11-12",
        "Source_Printed_Pages":
            "Financial Statements: 10-11",

        "Gross_Loans_Source_PDF_Page": "91-92",
        "NPL_Source_PDF_Page": "Annual Review: 3, 13",
        "Stage_3_Source_PDF_Pages": "53",
        "CAR_Source_PDF_Page": "Pillar 3: 10-11",

        "Entity_Basis_Note": (
            "FAB consolidated group, post NBAD-FGB merger. "
            "Financial amounts are sourced from the original "
            "audited 2019 consolidated financial statements. "
            "Gross loans are sourced from Note 12, PDF pages "
            "91-92. Stage 3 gross exposure and impairment "
            "allowance are sourced from Note 5, PDF page 53. "
            "POCI exposure is separately disclosed and is not "
            "included in the Stage 3 figure. "
            "The NPL ratio and NIM are published in the "
            "2019 Annual Review, PDF page 13. "
            "Absolute NPL amount is omitted because it has "
            "not been independently verified. "
            "Regulatory capital and RWA are sourced from "
            "the 2019 Pillar 3 Report, PDF pages 10-11."
        ),

        "NPL_Ratio_Pct": published_npl_ratio,
        "CAR_Pct": car,
        "CIR_Pct": cir,

        "Previous_Year_Total_Assets_LCU_Millions":
            assets_2018,

        "Previous_Year_Total_Equity_LCU_Millions":
            equity_2018,

        "Previous_Year_Shareholders_Equity_LCU_Millions":
            shareholders_equity_2018,

        "Average_Total_Assets_LCU_Millions":
            average_assets,

        "Average_Total_Equity_LCU_Millions":
            average_equity,

        "Average_Shareholders_Equity_LCU_Millions":
            average_shareholders_equity,

        "Profit_Attributable_To_Shareholders_LCU_Millions":
            shareholders_profit,

        "ROA_Pct": roa,
        "ROE_Pct": roe,

        "Opening_Balance_Source":
            FINANCIAL_STATEMENTS,

        "Opening_Balance_Source_PDF_Page": "11",

        "ROA_Method":
            "Net profit / average total assets * 100",

        "ROE_Method": (
            "Profit attributable to shareholders / "
            "average shareholders equity * 100"
        ),

        "NIM_Pct": published_nim,
        "NIM_Source_Document": ANNUAL_REVIEW,
        "NIM_Source_PDF_Page": "13",
        "NIM_Method": "Published net interest margin",
    }

    return record


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the validated 2019 record to the CSV",
    )
    args = parser.parse_args()

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}"
        )

    existing = pd.read_csv(CSV_PATH)

    if len(existing.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Expected {EXPECTED_COLUMNS} columns, "
            f"found {len(existing.columns)}"
        )

    if "Year" not in existing.columns:
        raise ValueError("Missing Year column")

    years = pd.to_numeric(existing["Year"], errors="raise")

    if years.duplicated().any():
        raise ValueError("Existing CSV contains duplicate years")

    if (years == 2019).any():
        raise ValueError(
            "2019 already exists. No changes made."
        )

    expected_existing_years = {2020, 2021, 2022, 2023, 2024}

    if set(years.astype(int)) != expected_existing_years:
        raise ValueError(
            "Existing years differ from expected 2020-2024. "
            "No changes made."
        )

    record = build_2019_record()

    unknown_columns = set(record) - set(existing.columns)

    if unknown_columns:
        raise ValueError(
            f"Unknown columns in 2019 record: {unknown_columns}"
        )

    missing_columns = set(existing.columns) - set(record)

    if missing_columns:
        raise ValueError(
            f"Missing columns in 2019 record: {missing_columns}"
        )

    new_row = pd.DataFrame(
        [record],
        columns=existing.columns,
    )

    combined = pd.concat(
        [existing, new_row],
        ignore_index=True,
    )

    combined = combined.sort_values(
        "Year"
    ).reset_index(drop=True)

    if len(combined) != len(existing) + 1:
        raise ValueError("Unexpected number of records")

    if combined["Year"].duplicated().any():
        raise ValueError("Duplicate years after insertion")

    # Confirm all original records remain unchanged.
    original_rows = existing.sort_values(
        "Year"
    ).reset_index(drop=True)

    preserved_rows = combined[
        combined["Year"] != 2019
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(
        original_rows,
        preserved_rows,
        check_dtype=False,
    )

    print("=" * 65)
    print("FAB 2019 DATA VALIDATION")
    print("=" * 65)

    print("Original records:", len(existing))
    print("New records:", len(combined))
    print("Columns:", len(combined.columns))
    print("Years:", combined["Year"].tolist())

    print("\n2019 KEY INDICATORS")
    print("Total assets:", record["Total_Assets_LCU_Millions"])
    print("Net profit:", record["Net_Profit_LCU_Millions"])
    print("Gross loans:", record["Gross_Loans_LCU_Millions"])
    print("ROA:", record["ROA_Pct"])
    print("ROE:", record["ROE_Pct"])
    print("CIR:", record["CIR_Pct"])
    print("NPL ratio:", record["NPL_Ratio_Pct"])
    print("CAR:", record["CAR_Pct"])
    print("NIM:", record["NIM_Pct"])

    print("\nALL VALIDATIONS PASSED")

    if not args.write:
        print("\nDRY RUN ONLY")
        print("CSV has NOT been modified.")
        print("Run with --write to save the 2019 record.")
        return

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup_path = BACKUP_DIR / (
        f"FAB_before_2019_insertion_{timestamp}.csv"
    )

    shutil.copy2(CSV_PATH, backup_path)

    print("\nBackup created:", backup_path)

    combined.to_csv(
        CSV_PATH,
        index=False,
    )

    print("CSV updated:", CSV_PATH)
    print("2019 record inserted successfully.")


if __name__ == "__main__":
    main()
