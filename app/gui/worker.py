"""QThread 异步任务与信号槽桥接"""
from typing import List
from PySide6.QtCore import QThread, Signal
from app.core.merger import PDFMergerEngine


class MergeWorker(QThread):
    """异步 PDF 合并工作线程"""

    progress = Signal(int, int, str)  # 当前索引, 总数, 当前正在合并的文件名
    finished = Signal(str)            # 完成信号，传递输出路径
    error = Signal(str)               # 异常捕获信号

    def __init__(self, file_list: List[str], output_path: str):
        super().__init__()
        self.file_list = file_list
        self.output_path = output_path
        self._engine = PDFMergerEngine()

    def run(self):
        try:
            out_path = self._engine.merge(
                self.file_list,
                self.output_path,
                progress_callback=lambda idx, total, name: self.progress.emit(idx, total, name),
            )
            self.finished.emit(out_path)
        except InterruptedError:
            pass
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """取消任务"""
        self._engine.cancel()
