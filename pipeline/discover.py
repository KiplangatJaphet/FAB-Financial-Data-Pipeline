from pathlib import Path
from datetime import datetime
import re
import csv

from configs.bank_configs import (
    BANK_CONFIGS,
    PDF_ROOT,
    OUTPUT_ROOT,
    START_YEAR,
    END_YEAR,
)

def discover_reports():
    records = []

    for bank_code, config in BANK_CONFIGS.items():
        folder = PDF_ROOT / config["pdf_folder"]

        pdfs = (
            sorted(folder.glob("*.pdf"))
            if folder.exists()
            else []
        )

        for pdf in pdfs:
            years = sorted({
                int(year)
                for year in re.findall(
                    r"(?<!\d)(20\d{2})(?!\d)",
                    pdf.stem
                )
                if START_YEAR <= int(year) <= END_YEAR
            })

            records.append({
                "Bank": bank_code,
                "Filename": pdf.name,
                "Year": years[0] if len(years) == 1 else "",
                "Year_Status": (
                    "OK" if len(years) == 1
                    else "AMBIGUOUS" if years
                    else "UNKNOWN"
                ),
                "File_Size_Bytes": pdf.stat().st_size,
                "PDF_Path": str(pdf),
            })

    return records


def main():
    records = discover_reports()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = OUTPUT_ROOT / f"pipeline_pdf_inventory_{timestamp}.csv"

    columns = [
        "Bank", "Filename", "Year", "Year_Status",
        "File_Size_Bytes", "PDF_Path"
    ]

    with output.open("x", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

    print("\n========== PDF DISCOVERY REPORT ==========\n")

    for bank_code in BANK_CONFIGS:
        bank_records = [
            r for r in records
            if r["Bank"] == bank_code
        ]

        year_counts = {}

        for record in bank_records:
            if record["Year_Status"] == "OK":
                year = record["Year"]
                year_counts[year] = year_counts.get(year, 0) + 1

        found = set(year_counts)
        expected = set(range(START_YEAR, END_YEAR + 1))

        missing = sorted(expected - found)
        duplicates = sorted(
            year for year, count in year_counts.items()
            if count > 1
        )

        unknown = [
            r["Filename"] for r in bank_records
            if r["Year_Status"] != "OK"
        ]

        print(f"{bank_code}")
        print(f"  PDFs: {len(bank_records)}")
        print(f"  Years identified: {len(found)}")
        print(f"  Missing years: {missing or 'None'}")
        print(f"  Duplicate years: {duplicates or 'None'}")
        print(f"  Unresolved filenames: {unknown or 'None'}")
        print()

    print("Inventory:", output)
    print("Existing datasets: UNCHANGED")


if __name__ == "__main__":
    main()
