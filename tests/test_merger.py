"""单元测试：核心合并引擎与进度机制"""
import os
import tempfile
import pytest
from pypdf import PdfReader, PdfWriter
from app.core.merger import PDFMergerEngine, merge_pdf_files


def _create_sample_pdf(file_path: str, num_pages: int = 1):
    """辅助函数：创建指定页数的测试 PDF 文件"""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    with open(file_path, "wb") as f:
        writer.write(f)


def test_merge_pdf_files_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf1 = os.path.join(tmpdir, "a.pdf")
        pdf2 = os.path.join(tmpdir, "b.pdf")
        out_pdf = os.path.join(tmpdir, "output.pdf")

        _create_sample_pdf(pdf1, num_pages=2)
        _create_sample_pdf(pdf2, num_pages=3)

        progress_records = []

        def on_progress(cur, total, path):
            progress_records.append((cur, total, path))

        res_path = merge_pdf_files(
            [pdf1, pdf2],
            out_pdf,
            progress_callback=on_progress,
        )

        assert os.path.exists(res_path)
        assert len(progress_records) == 2
        assert progress_records[0] == (1, 2, pdf1)
        assert progress_records[1] == (2, 2, pdf2)

        reader = PdfReader(res_path)
        assert len(reader.pages) == 5


def test_merge_empty_file_list_raises_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "output.pdf")
        with pytest.raises(ValueError, match="待合并的 PDF 文件列表不能为空"):
            merge_pdf_files([], out_pdf)


def test_merge_nonexistent_file_raises_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "output.pdf")
        with pytest.raises(FileNotFoundError):
            merge_pdf_files(["/path/not/exist.pdf"], out_pdf)


def test_merge_cancellation():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf1 = os.path.join(tmpdir, "1.pdf")
        pdf2 = os.path.join(tmpdir, "2.pdf")
        out_pdf = os.path.join(tmpdir, "output.pdf")

        _create_sample_pdf(pdf1, 1)
        _create_sample_pdf(pdf2, 1)

        engine = PDFMergerEngine()

        def cancel_on_second(cur, total, path):
            if cur == 1:
                engine.cancel()

        with pytest.raises(InterruptedError, match="用户已取消合并任务"):
            engine.merge([pdf1, pdf2], out_pdf, progress_callback=cancel_on_second)
