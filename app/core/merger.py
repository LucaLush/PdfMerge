"""PDF 解析、合并核心引擎与进度统计（纯 Python，无 GUI 依赖）"""
import os
from typing import Callable, List, Optional
try:
    from pypdf import PdfMerger
except ImportError:
    from pypdf import PdfWriter as PdfMerger


class PDFMergerEngine:
    """PDF 合并引擎"""

    def __init__(self):
        self._is_cancelled = False

    def cancel(self):
        """标记取消合并任务"""
        self._is_cancelled = True

    def reset(self):
        """重置取消标记"""
        self._is_cancelled = False

    def merge(
        self,
        file_list: List[str],
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        按顺序合并 PDF 文件列表至目标路径。

        :param file_list: 待合并的 PDF 绝对路径列表
        :param output_path: 最终输出的 PDF 文件路径
        :param progress_callback: 回调函数，形如 callback(current_index, total_count, current_file)
        :param cancel_check: 取消判定回调，返回 True 则中止合并
        :return: 成功保存的文件绝对路径
        :raises ValueError: 文件列表为空或参数无效
        :raises InterruptedError: 用户主动取消
        """
        if not file_list:
            raise ValueError("待合并的 PDF 文件列表不能为空。")

        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        merger = PdfMerger()
        total = len(file_list)

        try:
            for idx, pdf_path in enumerate(file_list, 1):
                if self._is_cancelled or (cancel_check and cancel_check()):
                    raise InterruptedError("用户已取消合并任务。")

                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"未找到待合并的 PDF 文件: {pdf_path}")

                if progress_callback:
                    progress_callback(idx, total, pdf_path)

                merger.append(pdf_path)

            if self._is_cancelled or (cancel_check and cancel_check()):
                raise InterruptedError("用户已取消合并任务。")

            merger.write(output_path)
            return os.path.abspath(output_path)
        finally:
            merger.close()


def merge_pdf_files(
    file_list: List[str],
    output_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> str:
    """简易调用接口：合并 PDF 列表"""
    engine = PDFMergerEngine()
    return engine.merge(
        file_list,
        output_path,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
