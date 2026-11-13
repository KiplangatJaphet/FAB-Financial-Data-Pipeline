import csv
import re
from pathlib import Path
from collections import Counter
import pdfplumber

PDF_DIR = Path("pdfs/Al_Rajhi")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Al_Rajhi_NIM_batch_candidates.csv"
SUMMARY_FILE = OUTPUT_DIR / "Al_Rajhi_NIM_batch_summary.csv"

PATTERNS = {
    "Net_Financing": [
        r"^financing,\s*net\b",
        r"^financing\s+net\b",
    ],
    "SAMA_Mutajara": [
        r"^mutajara\s+with\s+sama\b",
    ],
    "Interbank_Mutajara": [
        r"^mutajara\b",
    ],
    "Government_SAMA_Murabaha": [
        r"^murabaha\s+with\s+(?:saudi\s+government|sama)",
    ],
    "Sukuk": [
        r"^sukuk\b",
    ],
    "Structured_Products": [
        r"^structured\s+products?\b",
    ],
    "Impairment_Allowance": [
        r"^less:\s*impairment\b",
        r"^less:\s*expected\s+credit\s+loss",
    ],
}

NUMBER = re.compile(
    r"(?<![A-Za-z0-9])"
    r"\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?"
    r"|(?<![A-Za-z0-9])\(?-?\d{4,}(?:\.\d+)?\)?"
)

YEAR_PATTERN = re.compile(r"20(?:0\d|1\d|2[0-4])")

def classify(line):
    cleaned = line.strip().lower()
    for category, patterns in PATTERNS.items():
        if any(re.search(p, cleaned) for p in patterns):
            return category
    return None

def get_numbers(line):
    return NUMBER.findall(line)

def detect_unit(text):
    low = text.lower()
    if "sar '000" in low or "sar ’000" in low:
        return "SAR_thousands"
    if "sar million" in low or "sar mn" in low:
        return "SAR_millions"
    return "UNKNOWN"

def extract_candidates(path):
    rows = []
    report_year_match = YEAR_PATTERN.search(path.stem)
    report_year = (
        int(report_year_match.group())
        if report_year_match else None
    )

    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            lines = text.splitlines()

            for line_number, line in enumerate(lines, 1):
                category = classify(line)
                if not category:
                    continue

                numbers = get_numbers(line)
                if not numbers:
                    continue

                context = "\n".join(
                    lines[max(0, line_number - 9):line_number]
                )
                unit = detect_unit(context + "\n" + line)

                rows.append({
                    "Report_Year": report_year,
                    "PDF_File": path.name,
                    "PDF_Page": page_number,
                    "Line_Number": line_number,
                    "Category": category,
                    "Raw_Numbers": " | ".join(numbers),
                    "Unit_Detected": unit,
                    "Raw_Text": line.strip(),
                    "Status": "REVIEW_REQUIRED",
                })

        return rows, total_pages

def main():
    files = sorted(PDF_DIR.glob("*.pdf"))

    if not files:
        print("ERROR: No PDFs found in", PDF_DIR)
        return

    print("=" * 65)
    print("AL RAJHI BANK - BATCH NIM DATA EXTRACTION")
    print("=" * 65)
    print("PDFs found:", len(files))

    all_rows = []
    summary = []

    for path in files:
        print("\nProcessing:", path.name, flush=True)

        try:
            rows, pages = extract_candidates(path)
            all_rows.extend(rows)

            summary.append({
                "PDF_File": path.name,
                "Total_Pages": pages,
                "Candidate_Rows": len(rows),
                "Status": "SCANNED",
            })

            print(" Pages:", pages)
            print(" Candidate rows:", len(rows), flush=True)

        except Exception as exc:
            summary.append({
                "PDF_File": path.name,
                "Total_Pages": "",
                "Candidate_Rows": 0,
                "Status": f"ERROR: {exc}",
            })
            print(" ERROR:", exc, flush=True)

    candidate_fields = [
        "Report_Year",
        "PDF_File",
        "PDF_Page",
        "Line_Number",
        "Category",
        "Raw_Numbers",
        "Unit_Detected",
        "Raw_Text",
        "Status",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=candidate_fields
        )
        writer.writeheader()
        writer.writerows(all_rows)

    with SUMMARY_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "PDF_File",
                "Total_Pages",
                "Candidate_Rows",
                "Status",
            ],
        )
        writer.writeheader()
        writer.writerows(summary)

    counts = Counter(
        row["Category"] for row in all_rows
    )

    print("\n" + "=" * 65)
    print("BATCH EXTRACTION COMPLETE")
    print("=" * 65)

    print("PDFs processed:", len(files))
    print("Candidate rows:", len(all_rows))

    print("\nCANDIDATES BY CATEGORY:")
    for category, count in sorted(counts.items()):
        print(f" {category}: {count}")

    available_years = {
        int(m.group())
        for path in files
        if (m := YEAR_PATTERN.search(path.stem))
    }

    missing = sorted(
        set(range(2010, 2025)) - available_years
    )

    print("\nYears without a named PDF:", missing)
    print("\nCandidate file:", OUTPUT_FILE)
    print("Summary file:", SUMMARY_FILE)
    print("\nIMPORTANT:")
    print("Values are unverified candidate rows.")
    print("Comparative years and table columns are not assigned.")
    print("No NIM values have been calculated.")
    print("Main financial dataset has NOT been modified.")

if __name__ == "__main__":
    main()
