import pdfplumber

file = "pdfs/CBQ/CBQ_2019_Annual_Report.pdf"

with pdfplumber.open(file) as pdf:
    print(f"TOTAL PAGES: {len(pdf.pages)}")

    for i in [0, 1, 2, 3, 4, 5, 10, 20]:
        if i < len(pdf.pages):
            print(f"\n{'='*60}")
            print(f"PDF PAGE {i + 1}")
            print("="*60)
            print((pdf.pages[i].extract_text() or "")[:1500])
