"""QNB 2016 extraction module.

This module will hold the independently validated 2016 extraction
function before integration into extract_qnb.py.
"""

from pipeline.extract_qnb import (
    REPORT_CONFIG,
    read_pdf_page,
)
import pdfplumber


def extract_2016():
    """Placeholder for validated QNB 2016 extraction."""
    raise NotImplementedError(
        "2016 extraction logic has not yet been inserted."
    )
