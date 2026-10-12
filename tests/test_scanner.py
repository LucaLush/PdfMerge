"""单元测试：核心扫描与自然排序引擎"""
import os
import tempfile
from app.core.scanner import natural_sort_key, scan_pdf_files_in_folder


def test_natural_sort_key():
    filenames = ["10.pdf", "2.pdf", "1.pdf", "20.pdf", "file_2.pdf", "file_10.pdf", "file_1.pdf"]
    sorted_files = sorted(filenames, key=natural_sort_key)
    assert sorted_files == [
        "1.pdf",
        "2.pdf",
        "10.pdf",
        "20.pdf",
        "file_1.pdf",
        "file_2.pdf",
        "file_10.pdf",
    ]


def test_scan_pdf_files_in_nonexistent_folder():
    assert scan_pdf_files_in_folder("/path/does/not/exist") == []


def test_scan_pdf_files_in_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建乱序文件以及非 PDF 文件、子目录
        files_to_create = [
            "10.pdf",
            "1.PDF",
            "2.pdf",
            "document.txt",
            "readme.md",
        ]
        for name in files_to_create:
            file_path = os.path.join(tmpdir, name)
            with open(file_path, "wb") as f:
                f.write(b"%PDF-1.4 dummy content")

        # 创建子目录（不应被包含）
        os.makedirs(os.path.join(tmpdir, "subdir.pdf"), exist_ok=True)

        scanned = scan_pdf_files_in_folder(tmpdir)
        basenames = [os.path.basename(p) for p in scanned]

        assert basenames == ["1.PDF", "2.pdf", "10.pdf"]
