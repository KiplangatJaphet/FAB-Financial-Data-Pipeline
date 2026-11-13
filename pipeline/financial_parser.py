"""
Shared financial statement parsing utilities.

All extracted monetary values are returned in
local currency millions.
"""

import re


AMOUNT_PATTERN = r"\(?-?[\d,]+(?:\.\d+)?\)?|-"


def parse_amount(value, reporting_unit="thousands"):
    """
    Convert a financial amount into currency millions.

    Supported source units:
        units
        thousands
        millions
        billions
    """
    value = str(value).strip().replace(",", "")

    if value in {"-", "–", "—"}:
        return 0.0

    negative = (
        value.startswith("(")
        and value.endswith(")")
    )

    value = value.strip("()")

    number = float(value)

    divisors = {
        "units": 1_000_000,
        "thousands": 1_000,
        "millions": 1,
        "billions": 0.001,
    }

    unit = reporting_unit.lower().strip()

    if unit not in divisors:
        raise ValueError(
            f"Unsupported reporting unit: {reporting_unit}"
        )

    result = number / divisors[unit]

    return -result if negative else result


def extract_financial_value(
    text,
    label,
    reporting_unit="thousands",
    year_position=0,
):
    """
    Extract a labelled financial statement amount.

    year_position:
        0 = first numerical year column
        1 = second numerical year column

    Raises an error for missing or conflicting values.
    """
    if year_position not in (0, 1):
        raise ValueError("year_position must be 0 or 1")

    pattern = re.compile(
        rf"^{re.escape(label)}"
        rf"(?:\s+\d{{1,3}}(?:[.,]\d+)?)?"
        rf"\s+({AMOUNT_PATTERN})"
        rf"\s+({AMOUNT_PATTERN})"
        rf"(?:\s+{AMOUNT_PATTERN})*\s*$",
        re.IGNORECASE,
    )

    matches = []

    for line in text.splitlines():
        match = pattern.match(line.strip())

        if match:
            matches.append(
                parse_amount(
                    match.group(year_position + 1),
                    reporting_unit,
                )
            )

    if not matches:
        raise ValueError(
            f"Financial field not found: {label}"
        )

    if len(set(matches)) > 1:
        raise ValueError(
            f"Conflicting financial values: {label}: {matches}"
        )

    return matches[0]


def read_pdf_page(pdf, page_number):
    """
    Extract text from a one-based PDF page number.
    """
    if not 1 <= page_number <= len(pdf.pages):
        raise ValueError(
            f"Invalid PDF page: {page_number}"
        )

    text = pdf.pages[page_number - 1].extract_text()

    if not text:
        raise ValueError(
            f"No extractable text on PDF page {page_number}"
        )

    return text



def extract_table_total(text, label, reporting_unit="thousands"):
    """Extract the final amount from a multi-column financial row."""
    pattern = re.compile(
        rf"^{re.escape(label)}"
        rf"\s+((?:{AMOUNT_PATTERN})(?:\s+{AMOUNT_PATTERN})*)\s*$",
        re.IGNORECASE,
    )

    matches = []

    for line in text.splitlines():
        match = pattern.match(line.strip())

        if not match:
            continue

        values = re.findall(AMOUNT_PATTERN, match.group(1))

        if values:
            matches.append(
                parse_amount(values[-1], reporting_unit)
            )

    if not matches:
        raise ValueError(
            f"Financial table total not found: {label}"
        )

    if len(set(matches)) > 1:
        raise ValueError(
            f"Conflicting financial table totals: {label}"
        )

    return matches[0]
