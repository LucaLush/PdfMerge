"""全局配置、常量定义及版本号"""
import os
import sys

APP_NAME = "PDF 文件夹批量顺序合并工具"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"
DEFAULT_OUTPUT_FILENAME = "Merged_Output.pdf"

# 获取运行路径（支持 PyInstaller 单文件打包解压目录与源码目录）
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESOURCES_DIR = os.path.join(BASE_DIR, "app", "resources")
STYLE_PATH = os.path.join(RESOURCES_DIR, "styles.qss")
ICON_PATH = os.path.join(RESOURCES_DIR, "icon.ico")
