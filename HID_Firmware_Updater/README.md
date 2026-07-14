# HID 韌體更新工具

基於 **PySide6** + **hidapi** 的 HID 韌體更新 GUI 應用程式。

## 快速開始

```bash
# 建立虛擬環境
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell

# 安裝依賴
pip install -r requirements.txt

# 啟動應用程式
python main.py
```

## 專案結構

```
HID_Firmware_Updater/
├── main.py                 # 啟動入口
├── requirements.txt        # 依賴清單
├── .gitignore
├── README.md
├── src/                    # 核心原始碼
│   ├── __init__.py
│   ├── main_window.py      # 主視窗 UI 與事件處理
│   └── hid_worker.py       # HID 通訊背景 Worker
├── docs/                   # 開發文件
│   └── HID_Firmware_Updater_Guide.md
└── venv/                   # 虛擬環境 (不納入版本控制)
```

## 打包成執行檔

```bash
pyinstaller -F -w -n HIDFirmwareUpdater main.py
```

輸出檔案位於 `dist/HIDFirmwareUpdater.exe`。

## 清理專案

打包過程會產生許多暫存資料夾（如 `build/`, `dist/`, `__pycache__` 等）。您可以執行專案內附的清理腳本來還原乾淨的環境：

- **Windows**: 雙擊或在終端機執行 `clean.bat`
- *(這將自動刪除所有不必要的編譯與暫存檔案)*

## 詳細開發指南

請參閱 [docs/HID_Firmware_Updater_Guide.md](docs/HID_Firmware_Updater_Guide.md)。
