# PDF 文件夹批量顺序合并工具 (PDFMergerPro)

工业级多文件夹 PDF 批量顺序合并工具，采用 **PySide6 + pypdf** 开发，基于 MVC/MVVM 架构设计，支持外部文件夹拖拽、列表内部拖拽排序与上下移动、后台异步合并（避免界面卡顿）以及 GitHub Actions 自动化持续集成打包发布。

---

## 🌟 核心特性

- **自然人感知排序（Natural Sort）**：按数字自然顺序（如 `1.pdf`, `2.pdf`, `10.pdf`）自动扫描并排序文件夹内各 PDF 文件。
- **多文件夹顺序聚合**：支持添加多个文件夹，严格按照界面列表自上而下的视觉顺序汇总并合并。
- **拖拽与交互优化**：
  - 支持将外部文件夹直接拖入软件窗口或列表。
  - 列表项支持鼠标拖拽任意调换前后顺序，并配有「上移」、「下移」、「移除所选」、「清空列表」操作按钮及键盘 Delete 快捷键。
- **异步后台执行**：通过 `QThread` 线程执行合并，即使合并数百兆大文件主界面依然流畅不卡顿，并配有实时进度条与当前文件名反馈，支持中途取消。
- **工业级解耦架构**：业务核心（`core`）纯 Python 实现无 GUI 依赖，便于单独测试与复用；UI 表现层（`gui`）专注事件驱动与样式渲染。
- **CI/CD 自动化构建**：内置 GitHub Actions 自动化工作流，打标签（如 `v1.0.0`）即可自动运行测试并使用 PyInstaller 生成免安装 Windows 单文件 `PDFMergerPro.exe`。

---

## 📁 目录结构

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

## 🚀 快速上手

### 1. 安装依赖

```bash
# 创建并激活虚拟环境 (可选)
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

# 安装运行与测试依赖
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. 运行自动化测试

```bash
pytest tests/ -v
```

### 3. 启动图形界面

```bash
python main.py
```

---

## 📦 打包与交付

### 本地打包单文件可执行文件

使用 PyInstaller 配合规格文件构建：

```bash
pyinstaller --clean build_spec.spec
```

生成的文件将位于 `dist/PDFMergerPro` (或 `dist/PDFMergerPro.exe`)。

### GitHub Actions 自动化发布

推送到 GitHub 仓库并打上版本标签（Tag）：

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 将自动执行测试并在仓库 **Releases** 页面发布 Windows 单文件版 `PDFMergerPro.exe`。
