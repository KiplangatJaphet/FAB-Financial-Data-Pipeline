"""QNB 2016 consolidated financial data extraction.

All monetary values are converted from QAR thousands
to QAR millions.
"""

import re
import pdfplumber

from pipeline.extract_qnb import REPORT_CONFIG, read_pdf_page


def extract_2016():
    """Extract and validate QNB 2016 consolidated financial data."""

    config = REPORT_CONFIG[2016]
    pdf_path = config["pdf_path"]

    with pdfplumber.open(pdf_path) as pdf:
        balance = read_pdf_page(pdf, config["balance_page"])
        income = read_pdf_page(pdf, config["income_page"])
        capital = read_pdf_page(pdf, config["capital_page"])
        loans = read_pdf_page(pdf, config["loans_page"])
        ratios = read_pdf_page(pdf, config["ratios_page"])

    def amount(text, label, note=None):
        pattern = (
            r"^" + re.escape(label)
            + (r"\s+" + str(note) if note is not None else "")
            + r"\s+([\d,]+|\([\d,]+\))"
            + r"\s+(?:[\d,]+|\([\d,]+\)|[-?])$"
        )

        matches = [
            re.match(pattern, line.strip(), re.IGNORECASE)
            for line in text.splitlines()
        ]
        matches = [m for m in matches if m]

        if len(matches) != 1:
            raise ValueError(
                f"2016: Expected one match for '{label}', "
                f"found {len(matches)}"
            )

        value = matches[0].group(1)
        number = float(value.strip("()").replace(",", "")) / 1000
        return -number if value.startswith("(") else number

    record = {
        "Bank_Name": "QNB",
        "Country": "Qatar",
        "Year": 2016,
        "Reporting_Currency": "QAR",
        "Reporting_Unit": "Millions",
        "Source_Document": pdf_path.name,
        "Source_PDF_Page": 71,
        "Source_Printed_Pages": "69,70,95,101,107",
        "Gross_Loans_Source_PDF_Page": 103,
        "NPL_Source_PDF_Page": 103,
        "CAR_Source_PDF_Page": 97,
        "Entity_Basis_Note": (
            "QNB consolidated group; QCB Basel III; "
            "regulatory capital after proposed dividends; "
            "AT1 includes eligible QR10 billion instrument; "
            "Finansbank acquisition affects year-on-year comparability"
        ),
    }

    # BALANCE SHEET

    balance_fields = {
        "Total_Assets_LCU_Millions": ("Total assets", None),
        "Total_Liabilities_LCU_Millions": ("Total liabilities", None),
        "Total_Equity_LCU_Millions": ("Total equity", None),
        "Shareholders_Equity_LCU_Millions": (
            "Total equity attributable to equity holders of the Bank",
            None,
        ),
        "Loans_Advances_Islamic_Financing_LCU_Millions": (
            "Loans and advances to customers", 10
        ),
        "Customer_Accounts_Other_Deposits_LCU_Millions": (
            "Customer deposits", 17
        ),
    }

    for field, (label, note) in balance_fields.items():
        record[field] = amount(balance, label, note)

    # INCOME STATEMENT

    income_fields = {
        "Profit_Before_Taxation_LCU_Millions":
            "Profit before income taxes",
        "Total_Operating_Income_LCU_Millions":
            "Operating income",
        "Net_Interest_Income_LCU_Millions":
            "Net interest income",
        "Profit_Attributable_To_Shareholders_LCU_Millions":
            "Equity holders of the Bank",
    }

    for field, label in income_fields.items():
        record[field] = amount(income, label)

    profit_lines = [
        line for line in income.splitlines()
        if line.strip().startswith("Profit for the year ")
    ]

    if len(profit_lines) != 2 or profit_lines[0] != profit_lines[1]:
        raise ValueError("2016 profit disclosure inconsistent")

    record["Net_Profit_LCU_Millions"] = amount(
        profit_lines[0], "Profit for the year"
    )

    expenses = [
        ("Staff expenses", 30),
        ("Depreciation", 13),
        ("Other expenses", 31),
        ("Amortisation of intangible assets", None),
        ("Other provisions", None),
    ]

    record["Operating_Expenses_LCU_Millions"] = sum(
        amount(income, label, note)
        for label, note in expenses
    )

    record["Net_Impairment_Charge_LCU_Millions"] = sum([
        amount(
            income,
            "Net impairment losses on investment securities"
        ),
        amount(
            income,
            "Net impairment losses on loans and advances to customers",
            10,
        ),
    ])

    # GROSS LOANS - NOTE 10

    heading = "10. Loans and advances to customers"
    ending = "The aggregate amount of non-performing loans"

    if loans.count(heading) != 1 or ending not in loans:
        raise ValueError("2016 loan note boundaries not verified")

    loan_note = loans.split(heading, 1)[1].split(ending, 1)[0]

    loan_components = {
        "Loans": 493293.761,
        "Overdrafts": 34586.820,
        "Bills discounted": 3411.948,
    }

    for label, expected in loan_components.items():
        actual = amount(loan_note, label)
        if abs(actual - expected) > 0.001:
            raise ValueError(f"Loan component mismatch: {label}")

    record["Gross_Loans_LCU_Millions"] = sum(
        loan_components.values()
    )

    deferred_profit = amount(loan_note, "Deferred profit")
    allowance = amount(
        loan_note,
        "Allowance for impairment of loans and advances to customers"
    )

    if abs(
        record["Gross_Loans_LCU_Millions"]
        + deferred_profit
        + allowance
        - record["Loans_Advances_Islamic_Financing_LCU_Millions"]
    ) > 0.001:
        raise ValueError("Gross-to-net loans reconciliation failed")

    if not re.search(
        r"QR9,465 million.*?1\.8%",
        loans.replace("\n", " "),
        re.IGNORECASE
    ):
        raise ValueError("NPL disclosure not verified")

    record["Non_Performing_Loans_LCU_Millions"] = 9465.0
    record["NPL_Ratio_Pct"] = 1.8

    # REGULATORY CAPITAL

    cet1 = amount(
        capital, "Common Equity Tier 1 (CET 1) Capital"
    )
    at1_instrument = amount(
        capital, "Eligible Additional Tier 1 (AT1) Capital Instrument"
    )
    at1_other = amount(capital, "Additional Tier 1 Capital")
    tier2 = amount(capital, "Additional Tier 2 Capital")
    published_capital = amount(capital, "Total eligible capital")
    dividends = amount(capital, "Less: Proposed cash dividends")

    if abs(
        cet1 + at1_instrument + at1_other + tier2
        - published_capital
    ) > 0.001:
        raise ValueError("Published capital reconciliation failed")

    record["Eligible_Tier_1_Capital_LCU_Millions"] = (
        cet1 + dividends
    )
    record["Additional_Tier_1_Capital_LCU_Millions"] = (
        at1_instrument + at1_other
    )
    record["Tier_2_Capital_LCU_Millions"] = tier2
    record["Total_Regulatory_Capital_LCU_Millions"] = (
        published_capital + dividends
    )

    if abs(
        record["Eligible_Tier_1_Capital_LCU_Millions"]
        + record["Additional_Tier_1_Capital_LCU_Millions"]
        + record["Tier_2_Capital_LCU_Millions"]
        - record["Total_Regulatory_Capital_LCU_Millions"]
    ) > 0.001:
        raise ValueError("Adjusted capital reconciliation failed")

    # RISK-WEIGHTED ASSETS

    record["Credit_Risk_RWA_LCU_Millions"] = amount(
        capital, "Risk weighted assets for credit risk"
    )
    record["Market_Risk_RWA_LCU_Millions"] = amount(
        capital, "Risk weighted assets for market risk"
    )
    record["Operational_Risk_RWA_LCU_Millions"] = amount(
        capital, "Risk weighted assets for operational risk"
    )
    record["RWA_LCU_Millions"] = amount(
        capital, "Total risk weighted assets"
    )

    if abs(
        record["Credit_Risk_RWA_LCU_Millions"]
        + record["Market_Risk_RWA_LCU_Millions"]
        + record["Operational_Risk_RWA_LCU_Millions"]
        - record["RWA_LCU_Millions"]
    ) > 0.001:
        raise ValueError("RWA reconciliation failed")

    calculated_car = (
        record["Total_Regulatory_Capital_LCU_Millions"]
        / record["RWA_LCU_Millions"] * 100
    )

    if round(calculated_car, 1) != 16.0:
        raise ValueError("Published CAR does not reconcile")

    record["Published_CAR_Pct"] = 16.0
    record["CAR_Pct"] = 16.0

    if "30.4%" not in ratios:
        raise ValueError("Published CIR not verified")

    record["CIR_Pct"] = 30.4

    # OPENING BALANCES FROM 2015 COMPARATIVES

    opening_fields = {
        "Previous_Year_Total_Assets_LCU_Millions":
            ("Total assets", 538607.140),
        "Previous_Year_Total_Equity_LCU_Millions":
            ("Total equity", 62055.398),
        "Previous_Year_Shareholders_Equity_LCU_Millions": (
            "Total equity attributable to equity holders of the Bank",
            61103.305,
        ),
    }

    for field, (label, expected) in opening_fields.items():
        pattern = (
            r"^" + re.escape(label)
            + r"\s+[\d,]+\s+([\d,]+)$"
        )

        matches = [
            re.match(pattern, line.strip(), re.IGNORECASE)
            for line in balance.splitlines()
        ]
        matches = [m for m in matches if m]

        if len(matches) != 1:
            raise ValueError(f"Opening balance not unique: {label}")

        actual = float(
            matches[0].group(1).replace(",", "")
        ) / 1000

        if abs(actual - expected) > 0.001:
            raise ValueError(f"Opening balance mismatch: {label}")

        record[field] = actual

    # AVERAGE BALANCES

    for current, previous, average in [
        (
            "Total_Assets_LCU_Millions",
            "Previous_Year_Total_Assets_LCU_Millions",
            "Average_Total_Assets_LCU_Millions",
        ),
        (
            "Total_Equity_LCU_Millions",
            "Previous_Year_Total_Equity_LCU_Millions",
            "Average_Total_Equity_LCU_Millions",
        ),
        (
            "Shareholders_Equity_LCU_Millions",
            "Previous_Year_Shareholders_Equity_LCU_Millions",
            "Average_Shareholders_Equity_LCU_Millions",
        ),
    ]:
        record[average] = (
            record[current] + record[previous]
        ) / 2

    record["Opening_Balance_Source"] = pdf_path.name
    record["Opening_Balance_Source_PDF_Page"] = 71

    # CALCULATED PROFITABILITY RATIOS

    record["ROA_Pct"] = round(
        record["Net_Profit_LCU_Millions"]
        / record["Average_Total_Assets_LCU_Millions"] * 100,
        4,
    )

    record["ROE_Pct"] = round(
        record["Profit_Attributable_To_Shareholders_LCU_Millions"]
        / record["Average_Shareholders_Equity_LCU_Millions"] * 100,
        4,
    )

    record["ROA_Method"] = (
        "Net profit / average total assets * 100"
    )
    record["ROE_Method"] = (
        "Profit attributable to shareholders / "
        "average shareholders equity * 100"
    )

    # UNVERIFIED FIELDS

    record["NIM_Method"] = (
        "NIM not calculated: verified denominator unavailable"
    )

    # FINAL VALIDATION

    expected = {
        "Total_Assets_LCU_Millions": 719694.515,
        "Total_Liabilities_LCU_Millions": 648841.097,
        "Total_Equity_LCU_Millions": 70853.418,
        "Shareholders_Equity_LCU_Millions": 60023.250,
        "Net_Profit_LCU_Millions": 12404.279,
        "Profit_Before_Taxation_LCU_Millions": 13343.327,
        "Total_Operating_Income_LCU_Millions": 22907.788,
        "Net_Interest_Income_LCU_Millions": 17887.115,
        "Operating_Expenses_LCU_Millions": -7196.073,
        "Net_Impairment_Charge_LCU_Millions": -2545.312,
        "Gross_Loans_LCU_Millions": 531292.529,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 520417.231,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 506694.587,
        "Non_Performing_Loans_LCU_Millions": 9465.0,
        "Total_Regulatory_Capital_LCU_Millions": 62850.620,
        "RWA_LCU_Millions": 393899.971,
    }

    for field, expected_value in expected.items():
        if abs(record[field] - expected_value) > 0.001:
            raise ValueError(
                f"{field}: expected {expected_value}, "
                f"got {record[field]}"
            )

    if abs(
        record["Total_Assets_LCU_Millions"]
        - record["Total_Liabilities_LCU_Millions"]
        - record["Total_Equity_LCU_Millions"]
    ) > 0.001:
        raise ValueError("Balance sheet does not reconcile")

    return record
