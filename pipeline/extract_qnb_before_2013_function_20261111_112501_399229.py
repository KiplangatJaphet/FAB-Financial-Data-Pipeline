
import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

PDF_PATH = ROOT / "pdfs" / "QNB" / "QNB_2012_Annual_Report.pdf"

OUTPUT_PATH = ROOT / "output" / "QNB_raw_financial_data.csv"

BACKUP_DIR = ROOT / "output" / "backups"


# ---------------------------------------------------------
# REPORT CONFIGURATION
# PDF page numbers are 1-based.
# ---------------------------------------------------------

REPORT_CONFIG = {
    2013: {
        "pdf_path": ROOT / "pdfs" / "QNB" / "QNB_2013_Annual_Report.pdf",
        "balance_page": 41,
        "income_page": 42,
        "capital_page": 56,
        "loans_page": 59,
        "loans_detail_page": 60,
        "ratios_page": 39,
    },

    2011: {
        "pdf_path": ROOT / "pdfs" / "QNB" / "QNB_2011_Annual_Report.pdf",
        "balance_page": 40,
        "income_page": 40,
        "capital_page": 51,
        "loans_page": 52,
        "ratios_page": 37,
    },
    2012: {
        "balance_page": 39,
        "income_page": 40,
        "capital_page": 54,
        "loans_page": 57,
        "ratios_page": 37,
    }
}


# ---------------------------------------------------------
# NUMBER CONVERSION
# Original report figures are in thousands of QAR.
# Dataset figures are in millions of QAR.
# ---------------------------------------------------------

def parse_amount(value):
    value = str(value).strip().replace(",", "")

    negative = value.startswith("(") and value.endswith(")")

    value = value.replace("(", "").replace(")", "")

    number = float(value) / 1000

    return -number if negative else number


# ---------------------------------------------------------
# EXTRACT FINANCIAL ROWS
# ---------------------------------------------------------

def get_amount_with_note(text, label):
    """
    Extract the current-year amount from a labelled row.

    Handles:
    - Optional financial statement note numbers
    - Text from two-column PDF layouts
    - Repeated identical financial rows

    Rejects conflicting values.
    """

    amount = r"\(?[\d,]+\)?"

    pattern = (
        rf"(?im)(?<!\w){re.escape(label)}\s+"
        rf"(?:\d{{1,2}}\s+)?"
        rf"({amount})\s+({amount})(?=\s|$)"
    )

    matches = []

    for line in text.splitlines():
        # Prevent suffix matches such as:
        # "Other Operating Income" -> "Operating Income"
        #
        # Only accept a label when it begins the line
        # or follows text that does not form another
        # financial label.
        for match in re.finditer(pattern, line):
            prefix = line[:match.start()].strip()

            if prefix.endswith("Other"):
                continue

            matches.append(match.groups())

    if not matches:
        raise ValueError(
            f"No match found for {label!r}"
        )

    unique_matches = set(matches)

    if len(unique_matches) != 1:
        raise ValueError(
            f"Conflicting values for {label!r}: "
            f"{matches}"
        )

    return parse_amount(matches[0][0])


# ---------------------------------------------------------
# EXTRACT GROSS LOANS
# ---------------------------------------------------------

def get_gross_loans(loans_text):
    """
    Calculate gross loans from the relevant loans table.

    Gross Loans =
        Loans
        + Overdrafts
        + Bills Discounted
    """

    marker = "10. Loans and Advances to Customers"

    if marker not in loans_text:
        raise ValueError(
            "Loans and Advances to Customers note not found"
        )

    loan_section = loans_text.split(marker, 1)[1]

    loans = get_amount_with_note(loan_section, "Loans")

    overdrafts = get_amount_with_note(
        loan_section,
        "Overdrafts"
    )

    bills = get_amount_with_note(
        loan_section,
        "Bills Discounted"
    )

    gross_loans = loans + overdrafts + bills

    expected = 254518.739

    if abs(gross_loans - expected) > 0.01:
        raise ValueError(
            f"Gross loans validation failed: {gross_loans}"
        )

    return gross_loans


# ---------------------------------------------------------
# READ PDF PAGE
# ---------------------------------------------------------

def read_pdf_page(pdf, page_number):
    text = pdf.pages[page_number - 1].extract_text()

    if not text:
        raise ValueError(
            f"No extractable text on PDF page {page_number}"
        )

    return text


# ---------------------------------------------------------
# EXTRACT QNB 2012
# ---------------------------------------------------------

def extract_2012():

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Missing PDF: {PDF_PATH}"
        )

    config = REPORT_CONFIG[2012]

    with pdfplumber.open(PDF_PATH) as pdf:

        balance = read_pdf_page(
            pdf, config["balance_page"]
        )

        income = read_pdf_page(
            pdf, config["income_page"]
        )

        capital = read_pdf_page(
            pdf, config["capital_page"]
        )

        loans = read_pdf_page(
            pdf, config["loans_page"]
        )

        ratios = read_pdf_page(
            pdf, config["ratios_page"]
        )

    fields = {
        "Bank_Name": "QNB",
        "Country": "Qatar",
        "Year": 2012,
        "Reporting_Currency": "QAR",
        "Reporting_Unit": "Millions",
        "Source_Document": PDF_PATH.name,
        "Source_PDF_Page": 39,
        "Source_Printed_Pages": "75,76,105,111",
        "Gross_Loans_Source_PDF_Page": 57,
        "NPL_Source_PDF_Page": 57,
        "CAR_Source_PDF_Page": 54,
        "Entity_Basis_Note": "QNB consolidated group",
    }

    # -----------------------------------------------------
    # BALANCE SHEET
    # -----------------------------------------------------

    balance_labels = {
        "Total_Assets_LCU_Millions": "Total Assets",
        "Total_Liabilities_LCU_Millions": "Total Liabilities",
        "Total_Equity_LCU_Millions": "Total Equity",
        "Shareholders_Equity_LCU_Millions": (
            "Equity Attributable to Equity Holders of the Bank"
        ),
        "Loans_Advances_Islamic_Financing_LCU_Millions": (
            "Loans and Advances to Customers"
        ),
        "Customer_Accounts_Other_Deposits_LCU_Millions": (
            "Customer Deposits"
        ),
    }

    for column, label in balance_labels.items():
        fields[column] = get_amount_with_note(
            balance, label
        )

    # -----------------------------------------------------
    # INCOME STATEMENT
    # -----------------------------------------------------

    income_labels = {
        "Net_Profit_LCU_Millions": "Profit for the Year",
        "Profit_Before_Taxation_LCU_Millions": (
            "Profit Before Income Tax"
        ),
        "Total_Operating_Income_LCU_Millions": (
            "Operating Income"
        ),
        "Net_Interest_Income_LCU_Millions": (
            "Net Interest Income"
        ),
    }

    for column, label in income_labels.items():
        fields[column] = get_amount_with_note(
            income, label
        )

    # -----------------------------------------------------
    # OPERATING EXPENSES
    # -----------------------------------------------------

    staff = get_amount_with_note(
        income, "Staff Expenses"
    )

    depreciation = get_amount_with_note(
        income, "Depreciation"
    )

    other_expenses = get_amount_with_note(
        income, "Other Expenses"
    )

    fields["Operating_Expenses_LCU_Millions"] = -(
        staff + depreciation + other_expenses
    )

    # -----------------------------------------------------
    # IMPAIRMENT CHARGES
    # -----------------------------------------------------

    investment_impairment = get_amount_with_note(
        income,
        "Net Impairment (Losses) / Gains on Investment Securities"
    )

    loan_impairment = get_amount_with_note(
        income,
        "Net Impairment Losses on Loans and Advances to Customers"
    )

    fields["Net_Impairment_Charge_LCU_Millions"] = -(
        investment_impairment + loan_impairment
    )

    # -----------------------------------------------------
    # GROSS LOANS
    # -----------------------------------------------------

    fields["Gross_Loans_LCU_Millions"] = get_gross_loans(
        loans
    )

    # -----------------------------------------------------
    # NON-PERFORMING LOANS
    # -----------------------------------------------------

    if "3,380 million" not in loans:
        raise ValueError(
            "Unable to verify 2012 NPL amount"
        )

    if "1.3%" not in loans:
        raise ValueError(
            "Unable to verify 2012 NPL ratio"
        )

    fields["Non_Performing_Loans_LCU_Millions"] = 3380.0
    fields["NPL_Ratio_Pct"] = 1.3

    # -----------------------------------------------------
    # CAPITAL ADEQUACY
    # -----------------------------------------------------

    fields["Eligible_Tier_1_Capital_LCU_Millions"] = (
        get_amount_with_note(
            capital, "Total Eligible Tier 1 Capital"
        )
    )

    fields["Tier_2_Capital_LCU_Millions"] = 0.0  # Eligible Tier 2 capital

    fields["Total_Regulatory_Capital_LCU_Millions"] = (
        get_amount_with_note(
            capital, "Total Eligible Capital"
        )
    )

    fields["RWA_LCU_Millions"] = (
        get_amount_with_note(
            capital, "Risk Weighted Assets"
        )
    )

    if "21.0%" not in capital:
        raise ValueError(
            "Unable to verify published CAR"
        )

    fields["Published_CAR_Pct"] = 21.0
    fields["CAR_Pct"] = 21.0

    # -----------------------------------------------------
    # COST TO INCOME RATIO
    # -----------------------------------------------------

    if "16.8%" not in ratios:
        raise ValueError(
            "Unable to verify published CIR"
        )

    fields["CIR_Pct"] = 16.8

    # -----------------------------------------------------
    # OPENING BALANCES (2011 COMPARATIVES)
    # -----------------------------------------------------

    fields["Previous_Year_Total_Assets_LCU_Millions"] = (
        301955.331
    )

    fields["Previous_Year_Total_Equity_LCU_Millions"] = (
        42635.304
    )

    fields[
        "Previous_Year_Shareholders_Equity_LCU_Millions"
    ] = 42020.750

    fields["Average_Total_Assets_LCU_Millions"] = (
        fields["Total_Assets_LCU_Millions"]
        + fields["Previous_Year_Total_Assets_LCU_Millions"]
    ) / 2

    fields["Average_Total_Equity_LCU_Millions"] = (
        fields["Total_Equity_LCU_Millions"]
        + fields["Previous_Year_Total_Equity_LCU_Millions"]
    ) / 2

    fields["Average_Shareholders_Equity_LCU_Millions"] = (
        fields["Shareholders_Equity_LCU_Millions"]
        + fields[
            "Previous_Year_Shareholders_Equity_LCU_Millions"
        ]
    ) / 2

    fields["Profit_Attributable_To_Shareholders_LCU_Millions"] = (
        8338.822
    )

    fields["Opening_Balance_Source"] = PDF_PATH.name
    fields["Opening_Balance_Source_PDF_Page"] = 39

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    assets = fields["Total_Assets_LCU_Millions"]

    liabilities = fields[
        "Total_Liabilities_LCU_Millions"
    ]

    equity = fields["Total_Equity_LCU_Millions"]

    if abs(assets - (liabilities + equity)) > 0.01:
        raise ValueError(
            "Balance sheet does not balance: "
            f"{assets} != {liabilities} + {equity}"
        )

    expected_values = {
        "Total_Assets_LCU_Millions": 366853.832,
        "Net_Profit_LCU_Millions": 8423.040,
        "Total_Operating_Income_LCU_Millions": 11238.282,
        "Gross_Loans_LCU_Millions": 254518.739,
        "RWA_LCU_Millions": 173425.801,
    }

    for column, expected in expected_values.items():

        actual = fields[column]

        if abs(actual - expected) > 0.01:
            raise ValueError(
                f"Validation failed for {column}: "
                f"expected {expected}, got {actual}"
            )

    return fields


# ---------------------------------------------------------
# SAVE RECORD
# ---------------------------------------------------------


def extract_2011():
    """Extract and validate QNB 2011 consolidated financial data."""
    config = REPORT_CONFIG[2011]
    pdf_path = config["pdf_path"]

    with pdfplumber.open(pdf_path) as pdf:
        balance = read_pdf_page(pdf, config["balance_page"])
        capital = read_pdf_page(pdf, config["capital_page"])
        loans = read_pdf_page(pdf, config["loans_page"])
        ratios = read_pdf_page(pdf, config["ratios_page"])

    def amount(label, text=balance):
        return get_amount_with_note(text, label)

    record = {
        "Bank_Name": "QNB",
        "Country": "Qatar",
        "Year": 2011,
        "Reporting_Currency": "QAR",
        "Reporting_Unit": "Millions",
        "Source_Document": pdf_path.name,
        "Source_PDF_Page": 40,
        "Source_Printed_Pages": "76,77",
        "Gross_Loans_Source_PDF_Page": 52,
        "NPL_Source_PDF_Page": 52,
        "CAR_Source_PDF_Page": 51,
        "Entity_Basis_Note": "QNB consolidated group",

        "Total_Assets_LCU_Millions": amount("Total Assets"),
        "Total_Liabilities_LCU_Millions": amount("Total Liabilities"),
        "Total_Equity_LCU_Millions": amount("Total Equity"),
        "Shareholders_Equity_LCU_Millions": amount(
            "Total Equity Attributable to Equity Holders of the Bank"
        ),
        "Loans_Advances_Islamic_Financing_LCU_Millions": amount(
            "Loans and Advances and Financing Activities to Customers"
        ),
        "Customer_Accounts_Other_Deposits_LCU_Millions": amount(
            "Customer Deposits and Unrestricted Investment Accounts"
        ),
        "Net_Profit_LCU_Millions": amount("Profit for the Year"),
        "Profit_Before_Taxation_LCU_Millions": amount(
            "Profit Before Income Tax"
        ),
        "Total_Operating_Income_LCU_Millions": amount(
            "Operating Income"
        ),
    }

    # Net interest income is split across two PDF text lines.
    if "7,798,828 5,675,006" not in balance:
        raise ValueError("Net interest income source not verified")

    record["Net_Interest_Income_LCU_Millions"] = 7798.828

    expense_labels = [
        "General and Administrative Expenses",
        "Depreciation",
        "Amortisation of Intangible Assets",
        "Other (Provisions) / Recoveries",
    ]

    record["Operating_Expenses_LCU_Millions"] = sum(
        amount(label) for label in expense_labels
    )

    record["Net_Impairment_Charge_LCU_Millions"] = (
        amount("Net Impairment Losses on Loans and Advances")
        + amount(
            "Net Impairment Gains / (Losses) on Investment Securities"
        )
    )

    # Restrict parsing to the verified gross loans table.
    lines = loans.splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if line.strip().startswith(
            "Loans 188,752,220 124,759,567"
        )
    ]

    if len(matches) != 1:
        raise ValueError("Gross loans table not uniquely identified")

    section = "\n".join(lines[matches[0]:matches[0] + 3])

    record["Gross_Loans_LCU_Millions"] = sum(
        amount(label, section)
        for label in ["Loans", "Overdrafts", "Bills Discounted"]
    )

    # Published figures are checked against their source text.
    if "QR2,255 million" not in loans or "1.1%" not in loans:
        raise ValueError("NPL disclosure not verified")

    record["Non_Performing_Loans_LCU_Millions"] = 2255.0
    record["NPL_Ratio_Pct"] = 1.1

    if "15.7%" not in ratios:
        raise ValueError("Cost-to-income ratio not verified")

    record["CIR_Pct"] = 15.7

    # Prior-year comparative figures.
    record["Previous_Year_Total_Assets_LCU_Millions"] = 223382.447
    record["Previous_Year_Total_Equity_LCU_Millions"] = 24792.688
    record["Previous_Year_Shareholders_Equity_LCU_Millions"] = 24237.464

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

    record["Profit_Attributable_To_Shareholders_LCU_Millions"] = (
        7508.970
    )

    record["Opening_Balance_Source"] = pdf_path.name
    record["Opening_Balance_Source_PDF_Page"] = 40


    # Regulatory capital: QNB 2011, PDF page 51.
    regulatory_labels = {
        "Eligible_Tier_1_Capital_LCU_Millions":
            "Total Eligible Tier 1 Capital",
        "Total_Regulatory_Capital_LCU_Millions":
            "Total Eligible Capital",
        "RWA_LCU_Millions":
            "Risk Weighted Assets",
    }

    for column, label in regulatory_labels.items():
        record[column] = amount(label, capital)

    # The report shows a dash for eligible Tier 2 capital.
    if "Total Eligible Tier 2 Capital - -" not in capital:
        raise ValueError("Eligible Tier 2 capital disclosure not verified")

    record["Tier_2_Capital_LCU_Millions"] = 0.0

    if "Total Capital ratio 22.0% 15.3%" not in capital:
        raise ValueError("Published capital adequacy ratio not verified")

    record["Published_CAR_Pct"] = 22.0
    record["CAR_Pct"] = 22.0

    expected_capital = {
        "Eligible_Tier_1_Capital_LCU_Millions": 34357.737,
        "Total_Regulatory_Capital_LCU_Millions": 34357.737,
        "RWA_LCU_Millions": 156382.113,
    }

    for column, expected_value in expected_capital.items():
        if abs(record[column] - expected_value) > 0.001:
            raise ValueError(
                f"{column}: expected {expected_value}, "
                f"got {record[column]}"
            )

    # Balance sheet reconciliation.
    difference = (
        record["Total_Assets_LCU_Millions"]
        - record["Total_Liabilities_LCU_Millions"]
        - record["Total_Equity_LCU_Millions"]
    )

    if abs(difference) > 0.01:
        raise ValueError(
            f"2011 balance sheet reconciliation failed: {difference}"
        )

    expected = {
        "Total_Assets_LCU_Millions": 301955.331,
        "Net_Profit_LCU_Millions": 7553.997,
        "Gross_Loans_LCU_Millions": 196623.399,
        "Total_Operating_Income_LCU_Millions": 10184.092,
    }

    for column, value in expected.items():
        if abs(record[column] - value) > 0.01:
            raise ValueError(
                f"{column}: expected {value}, got {record[column]}"
            )

    return record


def save_record(record):

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Existing dataset not found: {OUTPUT_PATH}"
        )

    df = pd.read_csv(OUTPUT_PATH)

    bank = record["Bank_Name"]
    year = record["Year"]

    duplicate = (
        (df["Bank_Name"].astype(str) == bank)
        & (pd.to_numeric(df["Year"], errors="coerce") == year)
    )

    if duplicate.any():
        raise ValueError(
            f"{bank} {year} already exists in the dataset"
        )

    unknown_columns = set(record) - set(df.columns)

    if unknown_columns:
        raise ValueError(
            f"Unknown dataset columns: {unknown_columns}"
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"QNB_before_2012_{timestamp}.csv"
    )

    shutil.copy2(
        OUTPUT_PATH,
        backup_path
    )

    new_row = {
        column: record.get(column, pd.NA)
        for column in df.columns
    }

    updated = pd.concat(
        [df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    updated = updated.sort_values(
        ["Bank_Name", "Year"]
    )

    updated.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(f"Backup created: {backup_path}")
    print(f"Updated dataset: {OUTPUT_PATH}")
    print(f"Total rows: {len(updated)}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Extract QNB financial data"
    )

    parser.add_argument(
        "--year",
        type=int,
        required=True
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save validated extraction to CSV"
    )

    args = parser.parse_args()

    if args.year != 2012:
        raise ValueError(
            "Only QNB 2012 is currently configured"
        )

    record = extract_2012()

    print("\nQNB 2012 EXTRACTION RESULTS")
    print("=" * 60)

    for key, value in record.items():
        print(f"{key}: {value}")

    print("\nExtraction and validation completed.")

    if args.save:
        save_record(record)
    else:
        print(
            "\nRead-only mode: CSV was not modified."
        )


if __name__ == "__main__":
    main()




