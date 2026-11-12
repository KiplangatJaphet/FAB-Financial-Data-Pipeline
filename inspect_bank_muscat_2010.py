import re
import pdfplumber

pdf_path = "pdfs/Bank_Muscat/Bank_Muscat_2010_Annual_Report.pdf"

def decode_cid(text):
    def replace(match):
        number = int(match.group(1))
        code = number + 29

        if 32 <= code <= 126:
            return chr(code)

        if number == 3:
            return " "

        return match.group(0)

    return re.sub(r"\(cid:(\d+)\)", replace, text)

with pdfplumber.open(pdf_path) as pdf:
    for page_number in [11, 51, 76, 101]:
        text = pdf.pages[page_number - 1].extract_text() or ""

        print("\n" + "=" * 70)
        print("PDF PAGE:", page_number)
        print("=" * 70)
        print(decode_cid(text)[:2000])
