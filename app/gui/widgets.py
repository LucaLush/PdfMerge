"""自定义 UI 控件模块"""
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QListWidget


class FolderListWidget(QListWidget):
    """支持拖拽排序、按键快捷删除、外部拖拽文件夹的自定义列表控件"""

    folders_dropped = Signal(list)  # 信号：发射拖入的有效文件夹路径列表

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)

    def keyPressEvent(self, event: QKeyEvent):
        """支持按下 Delete 或 Backspace 键快速移除选中项"""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in self.selectedItems():
                self.takeItem(self.row(item))
            event.accept()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        """外部拖拽进入检测"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """外部拖拽移动中"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """拖拽释放处理：如果是外部文件/目录则提取文件夹，否则走内部项重排"""
        if event.mimeData().hasUrls():
            dirs = []
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if os.path.isdir(local_path):
                    dirs.append(local_path)
            if dirs:
                self.folders_dropped.emit(dirs)
                event.acceptProposedAction()
                return
        super().dropEvent(event)
