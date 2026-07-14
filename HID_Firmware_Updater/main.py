#!/usr/bin/env python3
"""HID 韌體更新工具 — 啟動入口"""
import sys
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()