from pathlib import Path
import pdfplumber

sources = {
    "NBK_2013_Financial_Statements.pdf": [3, 5],
    "NBK_2015_Annual_Report.pdf": [100, 102],
}

for filename, pages in sources.items():
    path = Path("pdfs/NBK") / filename

    print(f"\n{'=' * 75}")
    print("SOURCE:", filename)

    with pdfplumber.open(path) as pdf:
        for page_number in pages:
            print(f"\n{'-' * 75}")
            print("PDF PAGE:", page_number)
            print('-' * 75)

            text = pdf.pages[page_number - 1].extract_text() or ""
            print(text[:8500])
