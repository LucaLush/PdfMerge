"""Core logic package (Pure Python, no GUI dependencies)."""
from .scanner import natural_sort_key, scan_pdf_files_in_folder
from .merger import merge_pdf_files, PDFMergerEngine

__all__ = [
    "natural_sort_key",
    "scan_pdf_files_in_folder",
    "merge_pdf_files",
    "PDFMergerEngine",
]
