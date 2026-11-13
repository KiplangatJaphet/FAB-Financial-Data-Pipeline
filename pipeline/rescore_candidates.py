import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pdfplumber

from pipeline.classify import classify_page, decode_cid, ocr_page
from pipeline.discover import discover_reports
from configs.bank_configs import OUTPUT_ROOT


def main():
    files = sorted(
        OUTPUT_ROOT.glob("pipeline_statement_candidates_*.csv")
    )

    if not files:
        raise FileNotFoundError("No candidate CSV found.")

    source = files[-1]

    reports = {
        (r["Bank"], str(r["Year"]), Path(r["PDF_Path"]).name):
        Path(r["PDF_Path"])
        for r in discover_reports()
        if r["Year_Status"] == "OK"
    }

    with source.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    grouped = defaultdict(list)

    for row in rows:
        key = (
            row["Bank"],
            row["Year"],
            row["Source_Document"],
        )
        grouped[key].append(row)

    results = []

    for index, (key, candidates) in enumerate(
        grouped.items(), start=1
    ):
        if key not in reports:
            raise FileNotFoundError(
                f"Report not found in discovery: {key}"
            )

        path = reports[key]

        print(
            f"[{index}/{len(grouped)}] "
            f"{key[0]} {key[1]}",
            flush=True,
        )

        with pdfplumber.open(path) as pdf:
            cache = {}

            for row in candidates:
                page_number = int(row["PDF_Page"])
                method = row["Extraction_Method"]

                cache_key = (page_number, method)

                if cache_key not in cache:
                    page = pdf.pages[page_number - 1]

                    if method == "CID_Decoding":
                        text = decode_cid(
                            page.extract_text() or ""
                        )
                    elif method == "OCR_Tesseract":
                        text = ocr_page(page, side="left")
                    elif method == "PDF_Text":
                        text = page.extract_text() or ""
                    else:
                        raise ValueError(
                            f"Unknown extraction method: {method}"
                        )

                    cache[cache_key] = text

                score, headings, terms = classify_page(
                    cache[cache_key],
                    row["Statement"],
                )

                updated = dict(row)
                updated["Score"] = score
                updated["Heading_Matches"] = headings
                updated["Financial_Term_Matches"] = terms

                results.append(updated)

    ranked = defaultdict(list)

    for row in results:
        key = (
            row["Bank"],
            row["Year"],
            row["Statement"],
        )
        ranked[key].append(row)

    final = []

    for key, candidates in ranked.items():
        candidates.sort(
            key=lambda r: (
                -int(r["Score"]),
                int(r["PDF_Page"]),
            )
        )
        final.extend(candidates[:5])

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    output = OUTPUT_ROOT / (
        f"pipeline_statement_candidates_rescored_{timestamp}.csv"
    )

    with output.open(
        "x", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(final)

    print("\n========== RESCORING COMPLETE ==========")
    print("Reports processed:", len(grouped))
    print("Original candidates:", len(rows))
    print("Rescored candidates:", len(final))
    print("Output:", output)
    print("Existing financial datasets: UNCHANGED")


if __name__ == "__main__":
    main()
