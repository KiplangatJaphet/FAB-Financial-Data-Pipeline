from pathlib import Path
from datetime import datetime
import csv
import re
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

def classify_page(text, statement):
    normalised = " ".join(text.split()).lower()

    heading_matches = sum(
        bool(re.search(pattern, normalised, re.I))
        for pattern in PATTERNS[statement]
    )

    term_matches = sum(
        term in normalised
        for term in FINANCIAL_TERMS[statement]
    )

    score = heading_matches * 10 + term_matches

    return score, heading_matches, term_matches


def main():
    reports = [
        record for record in discover_reports()
        if record["Year_Status"] == "OK"
    ]

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = OUTPUT_ROOT / f"pipeline_statement_candidates_{timestamp}.csv"

    results = []

    print("\n========== STATEMENT CLASSIFICATION ==========\n")

    for index, report in enumerate(reports, start=1):
        path = Path(report["PDF_Path"])
        year = int(report["Year"])
        bank = report["Bank"]

        print(
            f"[{index}/{len(reports)}] "
            f"{bank} {year}: {path.name}",
            flush=True
        )

        candidates = {
            "Financial_Position": [],
            "Income_Statement": [],
        }

        try:
            with pdfplumber.open(path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""

                    for statement in candidates:
                        score, headings, terms = classify_page(
                            text, statement
                        )

                        if headings and terms >= 2:
                            candidates[statement].append({
                                "Bank": bank,
                                "Year": year,
                                "Source_Document": path.name,
                                "Statement": statement,
                                "PDF_Page": page_number,
                                "Score": score,
                                "Heading_Matches": headings,
                                "Financial_Term_Matches": terms,
                                "Preview": " ".join(text.split())[:300],
                            })

            for statement, pages in candidates.items():
                pages.sort(
                    key=lambda row: (
                        -row["Score"],
                        row["PDF_Page"]
                    )
                )
                results.extend(pages[:5])

                if pages:
                    best = pages[0]
                    print(
                        f"  {statement}: "
                        f"page {best['PDF_Page']} "
                        f"(score {best['Score']})"
                    )
                else:
                    print(f"  {statement}: NOT FOUND")

        except Exception as error:
            print(f"  ERROR: {type(error).__name__}: {error}")

    columns = [
        "Bank", "Year", "Source_Document",
        "Statement", "PDF_Page", "Score",
        "Heading_Matches", "Financial_Term_Matches",
        "Preview"
    ]

    with output.open("x", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

    print("\n========== CLASSIFICATION COMPLETE ==========\n")
    print("Reports attempted:", len(reports))
    print("Candidate pages:", len(results))
    print("Output:", output)
    print("Existing financial datasets: UNCHANGED")


if __name__ == "__main__":
    main()
