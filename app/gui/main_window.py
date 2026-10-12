"""交互主窗口模块"""
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_TITLE, DEFAULT_OUTPUT_FILENAME, ICON_PATH, STYLE_PATH
from app.core.scanner import scan_pdf_files_in_folder
from app.gui.widgets import FolderListWidget
from app.gui.worker import MergeWorker


class MainWindow(QMainWindow):
    """PDF 合并主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(760, 540)
        self.setAcceptDrops(True)
        self.worker = None

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self._init_ui()
        self._load_stylesheet()

    def _load_stylesheet(self):
        """加载自定义 QSS 样式表"""
        if os.path.exists(STYLE_PATH):
            try:
                with open(STYLE_PATH, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 操作工具栏
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加文件夹")
        self.btn_add.setObjectName("btnAdd")
        self.btn_add.clicked.connect(self.select_folder)

        self.btn_remove = QPushButton("移除所选")
        self.btn_remove.setObjectName("btnRemove")
        self.btn_remove.clicked.connect(self.remove_selected)

        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.setObjectName("btnClear")
        self.btn_clear.clicked.connect(self.clear_list)

        self.btn_move_up = QPushButton("上移")
        self.btn_move_up.setObjectName("btnMoveUp")
        self.btn_move_up.clicked.connect(self.move_up)

        self.btn_move_down = QPushButton("下移")
        self.btn_move_down.setObjectName("btnMoveDown")
        self.btn_move_down.clicked.connect(self.move_down)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_move_up)
        btn_layout.addWidget(self.btn_move_down)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 可拖拽排序列表
        self.list_widget = FolderListWidget()
        self.list_widget.folders_dropped.connect(self._on_folders_dropped)
        layout.addWidget(self.list_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # 状态提示
        self.status_label = QLabel("就绪：支持将文件夹直接拖入列表；长按项可上下拖拽调换合并顺序。")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        # 底部执行栏
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.cancel_merge)
        bottom_layout.addWidget(self.btn_cancel)

        self.btn_start = QPushButton("开始合并并保存")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setFixedHeight(36)
        self.btn_start.setStyleSheet("font-weight: bold;")
        self.btn_start.clicked.connect(self.start_merge)
        bottom_layout.addWidget(self.btn_start)

        layout.addLayout(bottom_layout)

    # 外部拖入目录支持
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        dirs = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                dirs.append(path)
        if dirs:
            self._on_folders_dropped(dirs)

    def _on_folders_dropped(self, dirs):
        for path in dirs:
            self._append_folder(path)

    def _append_folder(self, path: str):
        existing = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if path not in existing:
            self.list_widget.addItem(path)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含 PDF 的文件夹")
        if folder:
            self._append_folder(folder)

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def clear_list(self):
        self.list_widget.clear()

    def move_up(self):
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row - 1, item)
            self.list_widget.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0 and current_row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row + 1, item)
            self.list_widget.setCurrentRow(current_row + 1)

    def start_merge(self):
        total_folders = self.list_widget.count()
        if total_folders == 0:
            QMessageBox.warning(self, "提示", "请先添加至少一个待合并的文件夹！")
            return

        # 按列表自上而下的视觉顺序汇总 PDF
        all_pdf_files = []
        for i in range(total_folders):
            folder_path = self.list_widget.item(i).text()
            matched = scan_pdf_files_in_folder(folder_path)
            all_pdf_files.extend(matched)

        if not all_pdf_files:
            QMessageBox.warning(self, "提示", "所选的所有文件夹中均未找到有效 PDF 文件！")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并文件", DEFAULT_OUTPUT_FILENAME, "PDF 文件 (*.pdf)"
        )
        if not save_path:
            return

        # 锁定 UI 进入工作状态
        self.btn_start.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_move_up.setEnabled(False)
        self.btn_move_down.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.btn_cancel.setEnabled(True)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(all_pdf_files))
        self.progress_bar.setValue(0)

        self.worker = MergeWorker(all_pdf_files, save_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def cancel_merge(self):
        if self.worker and self.worker.isRunning():
            self.btn_cancel.setEnabled(False)
            self.status_label.setText("正在取消任务...")
            self.worker.cancel()

    def _on_progress(self, current, total, filename):
        self.progress_bar.setValue(current)
        self.status_label.setText(f"正在合并 ({current}/{total}): {os.path.basename(filename)}")

    def _on_finished(self, out_path):
        self._reset_ui_state()
        QMessageBox.information(self, "完成", f"PDF 合并已完成！\n保存路径：{out_path}")
        self.status_label.setText("合并已就绪。")

    def _on_error(self, err_msg):
        self._reset_ui_state()
        QMessageBox.critical(self, "错误", f"合并过程中发生异常：\n{err_msg}")
        self.status_label.setText("合并任务因异常中断。")

    def _reset_ui_state(self):
        self.btn_start.setEnabled(True)
        self.btn_add.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_move_up.setEnabled(True)
        self.btn_move_down.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(False)
