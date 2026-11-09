
from pathlib import Path
import pdfplumber
import pandas as pd

# Locate the test PDF
pdf_dir = Path("pdfs")
filename = "FAB_2024_Annual_Report.pdf"

pdf_files = list(pdf_dir.rglob(filename))

if not pdf_files:
    raise FileNotFoundError(f"Could not find {filename}")

pdf_path = pdf_files[0]

# Keywords we want to locate
keywords = [
    "statement of financial position",
    "statement of profit or loss",
    "total assets",
    "total equity",
    "net profit",
    "net interest income",
    "risk weighted assets",
    "capital adequacy",
    "non-performing loans",
]

results = []

with pdfplumber.open(pdf_path) as pdf:

    for page_number, page in enumerate(pdf.pages, start=1):

        text = page.extract_text() or ""
        text_lower = text.lower()

        matched_keywords = [
            word for word in keywords
            if word in text_lower
        ]

        results.append({
            "page": page_number,
            "text_length": len(text),
            "matched_keywords": ", ".join(matched_keywords),
        })

    df = pd.DataFrame(results)

    # Save page inspection results
    df.to_csv("output/FAB_2024_page_inventory.csv", index=False)

    print("\nPages with the most extractable text:")
    print(
        df.sort_values("text_length", ascending=False)
        .head(15)
        .to_string(index=False)
    )

    print("\nPages containing relevant financial keywords:")

    relevant = df[df["matched_keywords"] != ""]

    print(relevant.to_string(index=False))

    # Display sample text from the most readable page
    best_page_number = int(
        df["text_length"].idxmax()
    )

    print("\nSample text from the most readable page:")
    print(pdf.pages[best_page_number].extract_text()[:3000])
