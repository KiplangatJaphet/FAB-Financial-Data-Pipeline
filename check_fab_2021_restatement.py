
import pdfplumber
import re
from pathlib import Path

path = Path("pdfs/FAB/FAB_2022_Financial_Statements.pdf")

terms = [
    r"restat",
    r"reclassif",
    r"comparative figures",
    r"prior period",
    r"prior year adjustment",
    r"1,001,096,103",
    r"112,647,431",
]

with pdfplumber.open(path) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""

        matching_lines = [
            line.strip()
            for line in text.splitlines()
            if any(
                re.search(term, line, re.IGNORECASE)
                for term in terms
            )
        ]

        if matching_lines:
            print("\n" + "=" * 75)
            print(f"PDF PAGE: {page_number}")
            print("=" * 75)

            for line in matching_lines[:20]:
                print(line)

print("\nSEARCH COMPLETED")
