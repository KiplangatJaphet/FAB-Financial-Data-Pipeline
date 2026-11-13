
from pathlib import Path
from datetime import datetime
import csv
import re
import subprocess
import tempfile

import pdfplumber

from pipeline.discover import discover_reports
from configs.bank_configs import OUTPUT_ROOT


PATTERNS = {
    "Financial_Position": [
        r"consolidated\s+statement\s+of\s+financial\s+position",
        r"consolidated\s+balance\s+sheet",
        r"statement\s+of\s+financial\s+position",
        r"consolidated\s+statement\s+of\s+financial\s+condition",
    ],
    "Income_Statement": [
        r"consolidated\s+statement\s+of\s+income",
        r"consolidated\s+income\s+statement",
        r"consolidated\s+statement\s+of\s+profit\s+or\s+loss",
        r"consolidated\s+statement\s+of\s+profit\s+and\s+loss",
        r"statement\s+of\s+comprehensive\s+income",
    ],
}

FINANCIAL_TERMS = {
    "Financial_Position": [
        "total assets",
        "total liabilities",
        "total equity",
        "customer deposits",
        "cash and balances",
        "loans and advances",
        "financing receivables",
    ],
    "Income_Statement": [
        "net profit",
        "net income",
        "profit for the year",
        "interest income",
        "special commission income",
        "operating income",
        "operating expenses",
        "impairment",
    ],
}

# Verified PDF pages for reports requiring special handling.
SPECIAL_REPORTS = {
    ("BANK_MUSCAT", 2010): {
        "Financial_Position": 82,
        "Income_Statement": 83,
    },
    ("KFH", 2023): {
        "Financial_Position": 79,
        "Income_Statement": 78,
    },
}


def decode_cid(text):
    """Decode the CID character mapping found in Bank Muscat 2010."""

    def replace(match):
        value = int(match.group(1))

        if value <= 255:
            return chr((value + 29) % 256)

        return match.group(0)

    return re.sub(r"\(cid:(\d+)\)", replace, text)


def classify_page(text, statement):
    """Score candidate pages, prioritising primary financial statements."""

    normalised = " ".join(text.split()).lower()
    opening = normalised[:350]

    heading_matches = sum(
        bool(re.search(pattern, normalised, re.I))
        for pattern in PATTERNS[statement]
    )

    term_matches = sum(
        term in normalised
        for term in FINANCIAL_TERMS[statement]
    )

    score = heading_matches * 10 + term_matches

    primary_headings = {
        "Financial_Position": [
            r"consolidated statement of financial position",
            r"consolidated balance sheet",
            r"statement of financial position",
            r"consolidated statement of financial condition",
        ],
        "Income_Statement": [
            r"consolidated income statement",
            r"consolidated statement of income",
            r"consolidated statement of profit or loss",
            r"consolidated statement of profit and loss",
            r"statement of income",
            r"income statement",
            r"statement of profit or loss",
            r"statement of profit and loss",
        ],
    }

    if any(
        re.search(pattern, opening)
        for pattern in primary_headings[statement]
    ):
        score += 20

    if statement == "Income_Statement":
        if re.search(
            r"statement of (other )?comprehensive income",
            opening,
        ):
            score -= 25

    if re.search(
        r"notes to the (consolidated )?financial statements"
        r"|summary of significant accounting policies"
        r"|significant accounting policies",
        opening,
    ):
        score -= 20

    return score, heading_matches, term_matches


def ocr_page(page, side="left"):
    """OCR one half of a PDF page without saving permanent images."""

    midpoint = page.width / 2

    if side == "left":
        bounds = (0, 0, midpoint, page.height)
    else:
        bounds = (midpoint, 0, page.width, page.height)

    cropped = page.crop(bounds)

    with tempfile.TemporaryDirectory() as directory:
        image_path = Path(directory) / "page.png"

        cropped.to_image(resolution=300).save(image_path)

        result = subprocess.run(
            [
                "tesseract",
                str(image_path),
                "stdout",
                "-l",
                "eng",
                "--psm",
                "6",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout


def make_candidate(
    bank,
    year,
    path,
    statement,
    page_number,
    text,
    method,
):
    score, headings, terms = classify_page(text, statement)

    return {
        "Bank": bank,
        "Year": year,
        "Source_Document": path.name,
        "Statement": statement,
        "PDF_Page": page_number,
        "Score": score,
        "Heading_Matches": headings,
        "Financial_Term_Matches": terms,
        "Extraction_Method": method,
        "Preview": " ".join(text.split())[:300],
    }


def classify_report(report):
    path = Path(report["PDF_Path"])
    year = int(report["Year"])
    bank = report["Bank"]

    candidates = {
        "Financial_Position": [],
        "Income_Statement": [],
    }

    special_pages = SPECIAL_REPORTS.get((bank, year), {})

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):

            # The two exceptional reports use verified statement pages.
            if special_pages:
                if page_number not in special_pages.values():
                    continue

                if bank == "BANK_MUSCAT":
                    text = decode_cid(page.extract_text() or "")
                    method = "CID_Decoding"

                elif bank == "KFH":
                    text = ocr_page(page, side="left")
                    method = "OCR_Tesseract"

                else:
                    continue

                for statement, target_page in special_pages.items():
                    if page_number != target_page:
                        continue

                    candidate = make_candidate(
                        bank,
                        year,
                        path,
                        statement,
                        page_number,
                        text,
                        method,
                    )

                    # These pages were verified against the actual report.
                    # Still require a matching statement heading.
                    if candidate["Heading_Matches"] >= 1:
                        candidates[statement].append(candidate)

                continue

            # Standard classification for all other reports.
            text = page.extract_text() or ""

            for statement in candidates:
                score, headings, terms = classify_page(
                    text, statement
                )

                if headings and terms >= 2:
                    candidates[statement].append(
                        make_candidate(
                            bank,
                            year,
                            path,
                            statement,
                            page_number,
                            text,
                            "PDF_Text",
                        )
                    )

    return candidates


def main():
    reports = [
        record
        for record in discover_reports()
        if record["Year_Status"] == "OK"
    ]

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    output = (
        OUTPUT_ROOT
        / f"pipeline_statement_candidates_{timestamp}.csv"
    )

    results = []

    print("\n========== STATEMENT CLASSIFICATION ==========\n")

    for index, report in enumerate(reports, start=1):
        path = Path(report["PDF_Path"])
        year = int(report["Year"])
        bank = report["Bank"]

        print(
            f"[{index}/{len(reports)}] "
            f"{bank} {year}: {path.name}",
            flush=True,
        )

        try:
            candidates = classify_report(report)

            for statement, pages in candidates.items():
                pages.sort(
                    key=lambda row: (
                        -row["Score"],
                        row["PDF_Page"],
                    )
                )

                results.extend(pages[:5])

                if pages:
                    best = pages[0]

                    print(
                        f"  {statement}: "
                        f"page {best['PDF_Page']} "
                        f"(score {best['Score']}, "
                        f"{best['Extraction_Method']})"
                    )
                else:
                    print(f"  {statement}: NOT FOUND")

        except Exception as error:
            print(
                f"  ERROR: "
                f"{type(error).__name__}: {error}"
            )

    columns = [
        "Bank",
        "Year",
        "Source_Document",
        "Statement",
        "PDF_Page",
        "Score",
        "Heading_Matches",
        "Financial_Term_Matches",
        "Extraction_Method",
        "Preview",
    ]

    with output.open(
        "x",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n========== CLASSIFICATION COMPLETE ==========\n")
    print("Reports attempted:", len(reports))
    print("Candidate pages:", len(results))
    print("Output:", output)
    print("Existing financial datasets: UNCHANGED")


if __name__ == "__main__":
    main()
