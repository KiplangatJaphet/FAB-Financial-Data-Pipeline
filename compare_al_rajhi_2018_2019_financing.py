import pdfplumber
import pandas as pd
import re
from pathlib import Path

PDF_DIR = Path("pdfs/Al_Rajhi")
OUT_DIR = Path("output/verification/Al_Rajhi_NIM")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDFS = {
    2018: PDF_DIR / "Al_Rajhi_2018_Annual_Report.pdf",
    2019: PDF_DIR / "Al_Rajhi_2019_Annual_Report.pdf"
}

KEYWORDS = [
    "financing and advances",
    "financing and investment",
    "financing, net",
    "financing receivables",
    "gross financing",
    "allowance for impairment",
    "allowance for credit losses",
    "expected credit losses",
    "deferred income",
    "reclassification"
]

records = []
page_records = []

for report_year, pdf_path in PDFS.items():

    if not pdf_path.exists():
        raise SystemExit(f"Missing PDF: {pdf_path}")

    print(f"\nProcessing {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:

        print(f"Total pages: {len(pdf.pages)}")

        for page_index, page in enumerate(pdf.pages):

            text = page.extract_text() or ""
            lower = text.lower()

            matches = [
                keyword for keyword in KEYWORDS
                if keyword in lower
            ]

            if not matches:
                continue

            page_number = page_index + 1

            page_records.append({
                "Report_Year": report_year,
                "PDF_File": pdf_path.name,
                "PDF_Page": page_number,
                "Keywords": " | ".join(matches),
                "Full_Page_Text": text
            })

            lines = text.splitlines()

            for line_number, line in enumerate(lines):

                if any(
                    keyword in line.lower()
                    for keyword in KEYWORDS
                ):
                    context = "\n".join(
                        lines[
                            max(0, line_number - 2):
                            min(len(lines), line_number + 4)
                        ]
                    )

                    records.append({
                        "Report_Year": report_year,
                        "PDF_File": pdf_path.name,
                        "PDF_Page": page_number,
                        "Line_Number": line_number + 1,
                        "Source_Line": line,
                        "Context": context,
                        "Numeric_Tokens": " | ".join(
                            re.findall(
                                r"\(?-?\d[\d,]*(?:\.\d+)?\)?",
                                line
                            )
                        )
                    })

            print(
                f"Matched PDF page {page_number}: "
                f"{', '.join(matches[:3])}"
            )

lines_df = pd.DataFrame(records)
pages_df = pd.DataFrame(page_records)

lines_path = OUT_DIR / "Al_Rajhi_2018_2019_financing_note_lines.csv"
pages_path = OUT_DIR / "Al_Rajhi_2018_2019_financing_note_pages.csv"

lines_df.to_csv(
    lines_path,
    index=False,
    encoding="utf-8-sig"
)

pages_df.to_csv(
    pages_path,
    index=False,
    encoding="utf-8-sig"
)

# Reconciliation checkpoint
original_2018 = 234062.789
comparative_2018 = 231758.206
disclosed_reclassification = 1580.000

difference = original_2018 - comparative_2018
unexplained = difference - disclosed_reclassification

reconciliation = pd.DataFrame([{
    "Financial_Year": 2018,
    "Original_Net_Financing_SAR_Million": original_2018,
    "Comparative_Net_Financing_SAR_Million": comparative_2018,
    "Difference_SAR_Million": round(difference, 3),
    "Note37_Reclassification_SAR_Million": disclosed_reclassification,
    "Residual_SAR_Million": round(unexplained, 3),
    "Status": "REQUIRES_FINANCING_NOTE_VERIFICATION"
}])

reconciliation_path = (
    OUT_DIR / "Al_Rajhi_2018_financing_reconciliation.csv"
)

reconciliation.to_csv(
    reconciliation_path,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 65)
print("AL RAJHI - 2018/2019 FINANCING NOTE EXTRACTION")
print("=" * 65)
print("Matched source pages:", len(pages_df))
print("Matched source lines:", len(lines_df))
print()
print("2018 difference (SAR million):", round(difference, 3))
print("Note 37 reclassification:", disclosed_reclassification)
print("Unexplained residual:", round(unexplained, 3))
print()
print("FILES CREATED:")
print(lines_path)
print(pages_path)
print(reconciliation_path)
print()
print("Main financial CSV: NOT MODIFIED")
print("Earning-assets matrix: NOT MODIFIED")
print("=" * 65)
