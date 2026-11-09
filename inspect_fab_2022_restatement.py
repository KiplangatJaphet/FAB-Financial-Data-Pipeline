
import pdfplumber

path = "pdfs/FAB/FAB_2022_Financial_Statements.pdf"

with pdfplumber.open(path) as pdf:
    for page_number in [126, 127, 128]:
        print("\n" + "=" * 80)
        print(f"PDF PAGE: {page_number}")
        print("=" * 80)
        print(pdf.pages[page_number - 1].extract_text() or "")

print("\nRESTATEMENT INSPECTION COMPLETED")
