import os
import re
from typing import List


def natural_sort_key(s: str) -> list:
    """按数字人类自然感知顺序拆解排序键"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def scan_pdf_files_in_folder(folder_path: str) -> List[str]:
    """扫描指定文件夹内的一级 PDF 文件并进行自然排序"""
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return []

    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(folder_path, f))
    ]
    files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    return files
