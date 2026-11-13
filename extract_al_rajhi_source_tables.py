import csv
from pathlib import Path
import pdfplumber

PDF_DIR = Path("pdfs/Al_Rajhi")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Al_Rajhi_NIM_source_tables.csv"

KEYWORDS = [
    "mutajara with sama",
    "murabaha with sama",
    "murabaha with saudi government",
    "due from banks",
    "investments comprise",
    "financing, net",
    "structured products",
    "sukuk",
]

FIELDNAMES = [
    "PDF_File",
    "PDF_Page",
    "Table_Number",
    "Row_Number",
    "Cells",
]

def main():
    files = sorted(PDF_DIR.glob("*.pdf"))

    if not files:
        print("ERROR: No PDF files found in", PDF_DIR)
        return

    print("=" * 65)
    print("AL RAJHI - BATCH SOURCE TABLE EXTRACTION")
    print("=" * 65)
    print("PDFs found:", len(files))

    records = []
    errors = []

    for path in files:
        print("\nProcessing:", path.name, flush=True)
        count = 0

        try:
            with pdfplumber.open(path) as pdf:
                for page_no, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""

                    if not any(
                        keyword in text.lower()
                        for keyword in KEYWORDS
                    ):
                        continue

                    tables = page.extract_tables() or []

                    for table_no, table in enumerate(tables, 1):
                        if not table:
                            continue

                        for row_no, row in enumerate(table, 1):
                            cells = [
                                str(cell).strip()
                                if cell is not None else ""
                                for cell in row
                            ]

                            if not any(cells):
                                continue

                            records.append({
                                "PDF_File": path.name,
                                "PDF_Page": page_no,
                                "Table_Number": table_no,
                                "Row_Number": row_no,
                                "Cells": " | ".join(cells),
                            })

                            count += 1

            print(" Extracted table rows:", count, flush=True)

        except Exception as exc:
            errors.append((path.name, str(exc)))
            print(" ERROR:", exc, flush=True)

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES
        )
        writer.writeheader()
        writer.writerows(records)

    print("\n" + "=" * 65)
    print("BATCH SOURCE TABLE EXTRACTION COMPLETE")
    print("=" * 65)
    print("Reports found:", len(files))
    print("Extracted table rows:", len(records))
    print("Files with errors:", len(errors))

    if errors:
        print("\nERRORS:")
        for filename, error in errors:
            print(filename, ":", error)

    print("\nOutput:", OUTPUT_FILE)
    print("Main financial CSV: NOT MODIFIED")

if __name__ == "__main__":
    main()
