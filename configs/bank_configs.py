from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_ROOT = PROJECT_ROOT / "pdfs"
OUTPUT_ROOT = PROJECT_ROOT / "output"

START_YEAR = 2010
END_YEAR = 2024

BANK_CONFIGS = {
    "SNB": {
        "name": "Saudi National Bank",
        "country": "Saudi Arabia",
        "currency": "SAR",
        "pdf_folder": "SNB",
        "predecessor": "National Commercial Bank",
        "predecessor_code": "NCB",
        "merger_year": 2021,
        "output_file": "SNB_raw_financial_data.csv",
    },
    "SAB": {
        "name": "Saudi Awwal Bank",
        "country": "Saudi Arabia",
        "currency": "SAR",
        "pdf_folder": "SAB",
        "output_file": "SAB_raw_financial_data.csv",
    },
    "CBQ": {
        "name": "Commercial Bank of Qatar",
        "country": "Qatar",
        "currency": "QAR",
        "pdf_folder": "CBQ",
        "output_file": "CBQ_raw_financial_data.csv",
    },
    "BANK_MUSCAT": {
        "name": "Bank Muscat",
        "country": "Oman",
        "currency": "OMR",
        "pdf_folder": "Bank_Muscat",
        "output_file": "Bank_Muscat_raw_financial_data.csv",
    },
    "KFH": {
        "name": "Kuwait Finance House",
        "country": "Kuwait",
        "currency": "KWD",
        "pdf_folder": "KFH",
        "output_file": "KFH_raw_financial_data.csv",
    },
}

def get_bank_config(bank_code):
    code = bank_code.upper()

    if code not in BANK_CONFIGS:
        raise ValueError(f"Unsupported bank: {bank_code}")

    return BANK_CONFIGS[code]


if __name__ == "__main__":
    print("\n========== BANK CONFIGURATION ==========\n")

    for code, config in BANK_CONFIGS.items():
        folder = PDF_ROOT / config["pdf_folder"]

        pdf_count = (
            len(list(folder.glob("*.pdf")))
            if folder.exists()
            else 0
        )

        print(
            f"{code}: "
            f"{config['name']} | "
            f"{config['currency']} | "
            f"{pdf_count} PDFs"
        )

    print("\nConfigured banks:", len(BANK_CONFIGS))
    print("Research period:", START_YEAR, "-", END_YEAR)
    print("Existing datasets: UNCHANGED")
