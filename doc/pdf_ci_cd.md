# 工业级多文件夹 PDF 批量顺序合并工具技术方案与工程落地规范

本方案专为打造稳定、高可用且具备持续交付（CI/CD）能力的桌面端工具设计。采用 **PySide6 + PyMuPDF / pypdf** 技术栈，遵循 **MVC/MVVM 模块化解耦架构**，配置后台工作线程避免大文件合并卡顿，并集成 **GitHub Actions** 自动化构建 Windows `.exe` 安装包与便携版单文件。

---

## 1. 系统架构与工程目录结构

单文件脚本无法满足日志排查、异步处理、多平台样式统一以及长期维护需求。本项目采用分层结构，解耦 UI 渲染、业务核心逻辑与异步事件通信。

```text
pdf-folder-merger/
├── .github/
│   └── workflows/
│       └── build-release.yml    # GitHub Actions 自动化构建与 Release 脚本
├── app/
│   ├── __init__.py
│   ├── config.py                # 全局配置、常量定义及版本号
│   ├── core/                    # 业务核心层（纯 Python，无 GUI 依赖）
│   │   ├── __init__.py
│   │   ├── scanner.py           # 目录递归/遍历与自然排序算法
│   │   └── merger.py            # PDF 解析、合并核心引擎与进度统计
│   ├── gui/                     # UI 表现层（Qt 组件）
│   │   ├── __init__.py
│   │   ├── main_window.py       # 主窗口与拖拽交互
│   │   ├── widgets.py           # 自定义拖拽重排序列表控件
│   │   └── worker.py            # QThread 异步任务与信号槽桥接
│   └── resources/               # 静态资源
│       ├── icon.ico             # 应用程序图标
│       └── styles.qss           # 扁平化深色/浅色 QSS 样式表
├── tests/                       # 单元测试
│   ├── test_scanner.py
│   └── test_merger.py
├── .gitignore
├── pyproject.toml               # 项目元数据与依赖定义
├── requirements.txt             # 运行时依赖清单
├── requirements-dev.txt         # 开发与打包依赖
├── build_spec.spec              # PyInstaller 打包规格文件
└── main.py                      # 应用程序入口
```

---

## 2. 依赖定义

### `requirements.txt`
```text
PySide6>=6.6.0
pypdf>=4.0.0
```

### `requirements-dev.txt`
```text
pytest>=8.0.0
pyinstaller>=6.4.0
```

---

## 3. 核心模块实现

### 3.1 核心扫描与自然排序引擎 (`app/core/scanner.py`)
保证文件读取严格遵循用户逻辑预期（如 `2.pdf` 必须在 `10.pdf` 前面）。

```python
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
```

---

### 3.2 异步工作线程 (`app/gui/worker.py`)
防止合并数百兆的大型 PDF 时主界面无响应（未响应/卡死），通过 Qt Signal 实时上报进度与错误。

```python
from PySide6.QtCore import QThread, Signal
from pypdf import PdfMerger
from typing import List

class MergeWorker(QThread):
    progress = Signal(int, int, str)  # 当前索引, 总数, 当前正在合并的文件名
    finished = Signal(str)            # 完成信号，传递输出路径
    error = Signal(str)               # 异常捕获信号

    def __init__(self, file_list: List[str], output_path: str):
        super().__init__()
        self.file_list = file_list
        self.output_path = output_path
        self._is_cancelled = False

    def run(self):
        merger = PdfMerger()
        total = len(self.file_list)
        try:
            for idx, pdf_path in enumerate(self.file_list, 1):
                if self._is_cancelled:
                    merger.close()
                    return
                
                self.progress.emit(idx, total, pdf_path)
                merger.append(pdf_path)

            merger.write(self.output_path)
            merger.close()
            self.finished.emit(self.output_path)
        except Exception as e:
            merger.close()
            self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
```

---

### 3.3 交互主窗口 (`app/gui/main_window.py`)
支持外部文件夹物理拖入窗口、列表内部拖拽调整顺序，具备明确的执行状态反馈。

```python
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QFileDialog, QMessageBox,
    QLabel, QProgressBar, QAbstractItemView
)
from app.core.scanner import scan_pdf_files_in_folder
from app.gui.worker import MergeWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 文件夹批量顺序合并工具 v1.0.0")
        self.resize(720, 520)
        self.setAcceptDrops(True)
        self.worker = None

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 操作工具栏
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加文件夹")
        self.btn_add.clicked.connect(self.select_folder)
        
        self.btn_remove = QPushButton("移除所选")
        self.btn_remove.clicked.connect(self.remove_selected)
        
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.clicked.connect(self.clear_list)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 可拖拽排序列表
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)

        # 进度与状态区
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪：支持将文件夹直接拖入列表；长按项可上下拖拽调换合并顺序。")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        # 底部执行栏
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_start = QPushButton("开始合并并保存")
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
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
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
            self, "保存合并文件", "Merged_Output.pdf", "PDF 文件 (*.pdf)"
        )
        if not save_path:
            return

        # 锁定 UI 进入工作状态
        self.btn_start.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(all_pdf_files))
        self.progress_bar.setValue(0)

        self.worker = MergeWorker(all_pdf_files, save_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

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
        self.progress_bar.setVisible(False)
```

---

### 3.4 程序入口 (`main.py`)

```python
import sys
from PySide6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 4. GitHub Actions 自动化持续集成与打包交付

通过 GitHub 提供的 Windows 虚拟环境（`windows-latest`），无需本地配置复杂的 MSVC 或交叉编译工具链。当推送到 `main` 分支或打上版本 Tag 时，自动执行测试、PyInstaller 构建，并将 `.exe` 直接上传为产物或发布至 Release。

### `.github/workflows/build-release.yml`

```yaml
name: Build and Release Windows Executable

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch: # 支持手动一键触发构建

jobs:
  build-windows:
    runs-on: windows-latest

    steps:
      - name: 检出代码仓库
        uses: actions/checkout@v4

      - name: 配置 Python 环境
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 安装项目依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: 执行自动化单元测试
        run: |
          pytest tests/ --maxfail=1 --disable-warnings -q

      - name: 使用 PyInstaller 打包单文件可执行程序
        shell: pwsh
        run: |
          pyinstaller `
            --noconsole `
            --onefile `
            --name "PDFMergerPro" `
            --clean `
            main.py

      - name: 上传构建产物 (Artifacts)
        uses: actions/upload-artifact@v4
        with:
          name: PDFMergerPro-Windows-x64
          path: dist/PDFMergerPro.exe

      - name: 创建 GitHub Release 并附带 EXE (仅限 Tag 触发)
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: dist/PDFMergerPro.exe
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 5. 项目使用与交付工作流

1. **本地调试**：
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   python main.py
   ```
2. **提交发布**：
   在本地开发完毕后打上版本标签并推送：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. **获取程序**：
   推送到 GitHub 后，Actions 会在 2-3 分钟内自动完成打包，并直接在仓库的 **Releases** 页面生成 `PDFMergerPro.exe`，用户下载即可单文件双击运行，彻底摆脱环境配置。