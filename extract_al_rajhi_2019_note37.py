import pdfplumber
from pathlib import Path

pdf = Path("pdfs/Al_Rajhi/Al_Rajhi_2019_Annual_Report.pdf")
output = Path("output/verification/Al_Rajhi_NIM/Al_Rajhi_2019_Note37_full.txt")

with pdfplumber.open(pdf) as document:
    with output.open("w", encoding="utf-8") as file:
        for page_number in range(83, 87):
            page = document.pages[page_number - 1]

            text = page.extract_text(
                layout=True,
                x_tolerance=2,
                y_tolerance=3
            ) or ""

            file.write(f"\n{'=' * 75}\n")
            file.write(f"PDF PAGE {page_number}\n")
            file.write(f"{'=' * 75}\n")
            file.write(text)
            file.write("\n")

            print(f"Extracted PDF page {page_number}")

print(f"\nSaved to: {output}")
print("Main financial CSV: NOT MODIFIED")
