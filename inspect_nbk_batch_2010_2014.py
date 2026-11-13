from pathlib import Path
import pdfplumber

folder = Path("pdfs/NBK")

files = sorted(
    p for p in folder.glob("*.pdf")
    if "2012" in p.name or "2013" in p.name
    or "2014" in p.name
)

for path in files:
    print(f"\n========== {path.name} ==========")

    with pdfplumber.open(path) as pdf:
        print("Total pages:", len(pdf.pages))

        matches = []

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            heading = " ".join(text.splitlines()[:8]).lower()

            if (
                "consolidated statement of income" in heading
                or "consolidated statement of financial position" in heading
            ):
                matches.append(i + 1)

                print(f"\nPDF PAGE {i + 1}")
                print(text[:1300])

        if not matches:
            print("No consolidated statement headings detected.")

