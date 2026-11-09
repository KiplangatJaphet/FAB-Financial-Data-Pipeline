
from pathlib import Path
import pdfplumber
import pandas as pd

# Directory containing the PDF files
PDF_DIR = Path("pdfs")

results = []

# Find all PDF files, including those in subfolders
for pdf_file in PDF_DIR.rglob("*.pdf"):

    try:
        with pdfplumber.open(pdf_file) as pdf:

            total_pages = len(pdf.pages)

            # Inspect the first page
            first_page_text = pdf.pages[0].extract_text() or ""

            results.append({
                "filename": pdf_file.name,
                "bank_folder": pdf_file.parent.name,
                "total_pages": total_pages,
                "first_page_text_length": len(first_page_text),
                "text_sample": first_page_text[:200],
            })

    except Exception as error:
        results.append({
            "filename": pdf_file.name,
            "bank_folder": pdf_file.parent.name,
            "total_pages": None,
            "first_page_text_length": 0,
            "text_sample": str(error),
        })

# Convert results into a DataFrame
df = pd.DataFrame(results)

# Save the inspection results
df.to_csv("pdf_inventory.csv", index=False)

print(df[[
    "filename",
    "total_pages",
    "first_page_text_length"
]])

print(f"\nTotal PDFs inspected: {len(df)}")
