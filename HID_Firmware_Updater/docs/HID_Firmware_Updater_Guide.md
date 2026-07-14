# PySide6 HID 韌體更新工具開發指南

這份指南將帶你從零開始，使用 **PySide6** + **Qt Designer** + **VSCode** 開發一個具備 HID 通訊功能的 GUI 應用程式，並最終打包成獨立的 `.exe` 執行檔。

---

## 📋 目錄

1. [環境準備](#1-環境準備)
2. [使用 Qt Designer 設計 GUI](#2-使用-qt-designer-設計-gui)
3. [將 UI 轉換為 Python 程式碼](#3-將-ui-轉換為-python-程式碼)
4. [在 VSCode 中開發主程式](#4-在-vscode-中開發主程式)
5. [整合 HID 通訊範例](#5-整合-hid-通訊範例)
6. [封裝與發布：基礎打包 (PyInstaller)](#6-封裝與發布基礎打包-pyinstaller)
7. [封裝與發布：進階壓縮與最佳化](#7-封裝與發布進階壓縮與最佳化)
8. [封裝與發布：終極方案 (Nuitka)](#8-封裝與發布終極方案-nuitka)
9. [常見問題與排錯](#9-常見問題與排錯)
10. [清理專案暫存檔案](#10-清理專案暫存檔案)
11. [專案結構建議](#11-專案結構建議)
12. [總結](#12-總結)

---

## 1. 環境準備

### 1.1 安裝 Python
- 下載並安裝 Python 3.8 以上版本（[官方下載](https://www.python.org/downloads/)）
- 安裝時勾選 **「Add Python to PATH」**

### 1.2 安裝 VSCode 及擴充套件
- 下載 [VSCode](https://code.visualstudio.com/)
- 開啟 VSCode，安裝以下擴充套件（Ctrl+Shift+X）：
  - **Python** (by Microsoft)
  - **Qt for Python** (by Microsoft，提供 `.ui` 檔案語法高亮)

### 1.3 安裝所需 Python 套件
打開終端機（cmd / PowerShell / VSCode 終端），執行：
```bash
pip install pyside6 hidapi pyinstaller
```

- **pyside6**：Qt for Python 框架（包含 Qt Designer）
- **hidapi**：HID 通訊庫（在 Python 中以 `import hid` 載入，已內嵌 Windows 編譯好的二進位檔，無需額外安裝 `hidapi.dll`）
- **pyinstaller**：打包工具

---

## 2. 使用 Qt Designer 設計 GUI

### 2.1 啟動 Qt Designer
在終端機中輸入：
```bash
pyside6-designer
```
Qt Designer 視窗將會開啟。

### 2.2 建立一個主視窗
1. 點擊 **「Main Window」** 範本 → 建立
2. 從左側工具欄拖動以下元件到中央畫布：
   - **Line Edit**（用於輸入裝置 VID/PID）
   - **Push Button**（「連接設備」和「開始更新」）
   - **Progress Bar**（顯示進度）
   - **Text Edit**（顯示日誌資訊）

### 2.3 設定元件名稱（Object Name）
選取元件，在右下角 **屬性編輯器** 中修改 `objectName`，以便在程式中引用：
- `lineEdit_vid`
- `lineEdit_pid`
- `btn_connect`
- `btn_update`
- `progressBar`
- `textEdit_log`

### 2.4 儲存 UI 檔案
點擊 **File → Save**，將檔案儲存為 `mainwindow.ui`（建議放在專案根目錄）。

---

## 3. 將 UI 轉換為 Python 程式碼

### 3.1 使用 `pyside6-uic` 轉換
在終端機中執行：
```bash
pyside6-uic src/mainwindow.ui -o src/ui_mainwindow.py
```
此命令會產生一個 `src/ui_mainwindow.py` 檔案，內含 `Ui_MainWindow` 類別。

### 3.2 （可選）設定 VSCode 自動轉換
你可以在 VSCode 中建立工作區任務，每次儲存 `.ui` 時自動重新生成，但手動執行已足夠。

---

## 4. 在 VSCode 中開發主程式

### 4.1 建立主程式檔
在專案根目錄建立 `main.py`，這是應用程式的入口。

### 4.2 基本架構（載入 UI）
```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from src.ui_mainwindow import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 綁定按鈕事件
        self.ui.btn_connect.clicked.connect(self.on_connect)
        self.ui.btn_update.clicked.connect(self.on_update)

    def on_connect(self):
        vid = self.ui.lineEdit_vid.text()
        pid = self.ui.lineEdit_pid.text()
        self.ui.textEdit_log.append(f"嘗試連接 VID={vid}, PID={pid}")

    def on_update(self):
        self.ui.textEdit_log.append("開始更新...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### 4.3 測試執行
在終端機執行：
```bash
python main.py
```
應該會看到你的視窗，點擊按鈕會在日誌區顯示文字。

---

## 5. 整合 HID 通訊範例

為了避免 GUI 卡頓，HID 讀寫必須放在背景執行緒中（`QThread`）。以下是一個完整的範例，示範如何連接 HID 設備並模擬韌體更新。

### 5.1 建立 Worker 類別（放置於 `src/hid_worker.py`）
```python
# src/hid_worker.py
import hid
from PySide6.QtCore import QObject, Signal

class HIDWorker(QObject):
    # 定義信號，用於與主執行緒溝通
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)  # 成功與否, 訊息

    def __init__(self, vid, pid, firmware_path):
        super().__init__()
        self.vid = int(vid, 0) if vid.startswith('0x') else int(vid)
        self.pid = int(pid, 0) if pid.startswith('0x') else int(pid)
        self.firmware_path = firmware_path

    def run(self):
        try:
            self.log.emit("正在打開 HID 設備...")
            device = hid.device()
            device.open(self.vid, self.pid)
            self.log.emit("設備已連線")

            # 模擬讀取韌體檔案（這裡用模擬資料）
            # 實際專案請用 open(self.firmware_path, 'rb').read()
            firmware = bytes([0x00] * 1024)  # 模擬 1KB 韌體
            chunk_size = 64
            total = len(firmware)
            for i in range(0, total, chunk_size):
                chunk = firmware[i:i+chunk_size]
                # 第一個 byte 通常為 Report ID（此處假設為 0x00）
                report = bytes([0x00]) + chunk
                # 寫入 HID
                device.write(report)
                # 更新進度
                progress = int((i + chunk_size) / total * 100)
                self.progress.emit(min(progress, 100))
                # 模擬延遲
                import time
                time.sleep(0.01)

            device.close()
            self.log.emit("韌體更新完成！")
            self.finished.emit(True, "更新成功")
        except Exception as e:
            self.log.emit(f"錯誤：{e}")
            self.finished.emit(False, str(e))
```

### 5.2 修改 `main.py` 以使用 Worker
```python
# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QThread
from src.ui_mainwindow import Ui_MainWindow
from src.hid_worker import HIDWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.thread = None
        self.worker = None

        self.ui.btn_connect.clicked.connect(self.on_connect)
        self.ui.btn_update.clicked.connect(self.on_update)

    def on_connect(self):
        vid = self.ui.lineEdit_vid.text().strip()
        pid = self.ui.lineEdit_pid.text().strip()
        if not vid or not pid:
            self.ui.textEdit_log.append("請輸入 VID 和 PID")
            return
        # 簡單測試連接（僅驗證格式）
        self.ui.textEdit_log.append(f"準備連接 VID={vid}, PID={pid}")

    def on_update(self):
        # 選擇韌體檔案
        fname, _ = QFileDialog.getOpenFileName(self, "選擇韌體檔案", "", "Bin Files (*.bin);;All Files (*)")
        if not fname:
            return

        vid = self.ui.lineEdit_vid.text().strip()
        pid = self.ui.lineEdit_pid.text().strip()
        if not vid or not pid:
            self.ui.textEdit_log.append("請先輸入 VID 和 PID")
            return

        # 禁用按鈕防止重複點擊
        self.ui.btn_update.setEnabled(False)
        self.ui.progressBar.setValue(0)

        # 建立執行緒與 Worker
        self.thread = QThread()
        self.worker = HIDWorker(vid, pid, fname)
        self.worker.moveToThread(self.thread)

        # 連接信號
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.ui.textEdit_log.append)
        self.worker.progress.connect(self.ui.progressBar.setValue)
        self.worker.finished.connect(self.on_update_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.textEdit_log.append("開始更新...")

    def on_update_finished(self, success, msg):
        self.ui.btn_update.setEnabled(True)
        if success:
            self.ui.textEdit_log.append(f"✅ {msg}")
        else:
            self.ui.textEdit_log.append(f"❌ 失敗：{msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### 5.3 測試 HID 功能
- 請根據你的實際 HID 設備修改 `VID` / `PID` 及韌體格式。
- 如果沒有設備，可先註解掉 `device.open()` 等真實操作，用模擬數據測試執行緒機制。

---

## 6. 封裝與發布：基礎打包 (PyInstaller)

使用 **PyInstaller** 是 Python 專案中最常見的打包方式，可以將整個專案打包成一個獨立的 `.exe` 檔案。

### 6.1 使用自動化腳本打包 (推薦)
為了簡化打包流程，專案內提供了自動化腳本：
- **Windows**: `build_pyinstaller.bat`
- **Linux/Git Bash**: `build_pyinstaller.sh`

只需在終端機中執行腳本並傳入專案名稱：
```cmd
.\build_pyinstaller.bat HIDFirmwareUpdater
```
打包完成後，獨立的 `.exe` 檔案會自動輸出到 `dist` 資料夾中。

### 6.2 手動執行打包命令
如果您想手動執行，請在專案根目錄下輸入：
```bash
pyinstaller -F -w -n HIDFirmwareUpdater main.py
```
參數說明：
- `-F`：打包成單一檔案
- `-w`：隱藏控制台視窗（純 GUI 應用）
- `-n`：指定輸出檔名

### 6.3 打包後測試
在 `dist` 資料夾中找到 `HIDFirmwareUpdater.exe`，雙擊執行，應出現您的應用程式視窗。

---

## 7. 封裝與發布：進階壓縮與最佳化

產生的 `.exe` 檔案通常會有點大（包含 Python 環境與 Qt 庫）。這裡介紹兩種壓縮方案。

### 7.1 使用 UPX 壓縮執行檔 (build_upx)
UPX (Ultimate Packer for eXecutables) 可以在不改變執行方式的前提下，壓縮 `.exe` 的檔案大小。

1. 前往 [UPX 官方 GitHub Release](https://github.com/upx/upx/releases) 下載 Windows 版，將 `upx.exe` 放入 `tools` 資料夾。
2. 執行自動化腳本對 `dist` 資料夾內的執行檔進行最高等級壓縮：
   ```cmd
   .\build_upx.bat HIDFirmwareUpdater
   ```
*(注意：UPX 壓縮有時可能會被部分防毒軟體誤判為惡意程式，請依實際需求評估是否使用。UPX 本身允許免費應用於商業或閉源軟體)*

### 7.2 使用 7-Zip 製作極致壓縮自解檔 (build_7z)
現代 PyInstaller 的單一執行檔預設啟用了 Windows `GUARD_CF`，導致 UPX 容易壓縮失敗或被誤殺。
如果您想獲得**極致的小檔案**，強烈建議使用 **7-Zip SFX (自解壓縮)** 功能來取代 UPX。

**專案提供了 `build_7z.bat` 與 `build_7z.sh` 來全自動完成這件事：**
1. 確保 `tools` 資料夾下有 `7zS.sfx` (可從 7-Zip 官網的 Extra 包取得)，以及 `7z.exe`。
2. 執行自動化腳本：
   ```cmd
   .\build_7z.bat HIDFirmwareUpdater
   ```
腳本會自動使用 PyInstaller (資料夾模式) 打包、建立設定檔、使用 LZMA 最高壓縮率進行壓縮，最後合併為單一的 `_SFX.exe`。這不僅壓縮率遠勝 UPX，且防毒軟體誤判率極低。

---

## 8. 封裝與發布：終極方案 (Nuitka)

如果您追求的是**「啟動速度最快」、「防毒軟體最不會誤判」、「程式碼最難被反組譯」**，目前業界最專業的做法是使用 **Nuitka**。

### 8.1 Nuitka 原生編譯的優勢
PyInstaller 的本質是「壓縮檔」，執行時需先解壓；而 **Nuitka** 會將 Python 程式碼**轉換成 C 語言原始碼**，接著編譯成真正的機器碼二進位 `.exe`。
- **點擊瞬間啟動**：無需在背景解壓縮到暫存區。
- **極高的安全性**：幾乎無法被輕易反組譯回 `.py` 原始碼。

### 8.2 使用自動化腳本編譯 (build_nuitka)
1. 安裝套件：`pip install nuitka`
2. 執行專案提供的自動化腳本 (內建了 PySide6 最佳化參數，並自動輸出至 `dist` 資料夾)：
   ```cmd
   .\build_nuitka.bat HIDFirmwareUpdater
   ```
*(注意：Nuitka 的編譯過程可能耗時數分鐘至數十分鐘，且初次執行時會自動詢問並下載 MinGW C 編譯器環境)*

### 8.3 關於 Nuitka 與 PySide6 的商用授權說明
許多開發者擔心 Nuitka 編譯會違反開源授權。**簡單的答案是：不會，您可以合法且安心地將其用於商業閉源專案**。
1. **Nuitka 授權**：基於 Apache License 2.0，允許商業與閉源使用。
2. **Python 授權**：PSF License，允許商業閉源。
3. **第三方套件授權 (關鍵)**：
   - 本專案使用的 **`PySide6`** 是 **LGPL 授權**。LGPL 允許開發商業閉源軟體，**前提是必須使用動態連結 (Dynamic Linking)**。
   - Nuitka 預設會將 `PySide6` 等 C/C++ 庫保留為獨立的動態連結庫（`.pyd`, `.dll`）並動態呼叫，這完全符合 LGPL 的規範。

**結論**：只要您使用的是 `PySide6`，且沒有修改其底層 C++ 原始碼，您就可以合法地使用 Nuitka 將軟體編譯發布為商業閉源產品。（建議在軟體的「關於」頁面中聲明使用了 PySide6）

---

## 9. 常見問題與排錯

### Q1: 執行 `pyside6-designer` 找不到命令？
- 確保 Python Scripts 目錄已加入 PATH（可重新安裝 PySide6 或使用 `python -m PySide6.scripts.pyside6_designer` 替代）

### Q2: HID 設備無法打開？
- 檢查 VID/PID 是否正確（可透過 `hid.enumerate()` 枚舉設備）
- 確認設備驅動正常，且未被其他程式佔用
- Windows 可能需要管理員權限執行

### Q3: 打包後執行出現 `Failed to execute script` 錯誤？
- 在命令列執行 `.\dist\HIDFirmwareUpdater.exe` 查看具體錯誤訊息（通常缺少依賴的 `.dll` 檔案）
- 解決方式：在打包時加入 `--hidden-import` 或使用 `--add-data` 加入缺失的檔案

### Q4: 程式打包後體積過大？
- 可使用 `virtualenv` 建立乾淨環境，只安裝必要的套件，再進行打包
- 或使用 `UPX` 壓縮執行檔（請參考 **6.5 節**說明）

### Q5: 執行程式時出現 `ImportError: Unable to load any of the following libraries: hidapi.dll` 錯誤？
- 這是因為在 Python 環境中同時安裝了 `hid` 與 `hidapi` 套件。兩者都使用 `import hid` 作為載入名稱，但 `hid` 套件（基於 `ctypes`）需要系統已安裝並可尋找到 `hidapi.dll`，而 `hidapi` 套件則直接封裝了編譯好的二進位檔。
- **解決方法**：解除安裝衝突的套件，並僅重新安裝 `hidapi` 套件即可：
  ```bash
  pip uninstall hid hidapi
  pip install hidapi
  ```
- pip install hid 安裝的是 hid（一個基於 ctypes 的封裝，不包含 DLL，需要系統預先安裝 hidapi.dll）。

- pip install hidapi 安裝的是 hidapi（它直接綁定 hidapi 函式庫，並且在安裝時會自動將適當的 DLL 放到 site-packages/hidapi 目錄下）。  

- 當兩者同時存在時，import hid 會優先載入 hid 套件（因為它在 sys.path 中的順序可能更前），而 hid 套件會去搜尋系統 PATH 中的 hidapi.dll，而不是 hidapi 套件自帶的 DLL，因此就算 hidapi 套件已經把 DLL 放好，hid 套件也找不到，導致錯誤。因此 **強烈建議只安裝 hidapi**，不要同時安裝 hid。

---

## 10. 清理專案暫存檔案

在使用 PyInstaller 或 Nuitka 進行編譯後，專案目錄中會產生大量的暫存檔與資料夾（例如 `build/`, `dist/`, `.spec`, `__pycache__` 等）。這些檔案會佔用大量硬碟空間，且不應該被納入 Git 版本控制。

您可以透過執行專案目錄下提供的自動清理腳本，一鍵將專案還原成最乾淨的狀態：
- **Windows**: 雙擊或在終端機執行 `clean.bat`

*(腳本會自動尋找並安全地刪除所有與編譯相關的殘留檔案，不會影響您的核心程式碼)*

---

## 11. 專案結構建議
```
project/
├── main.py                 # 啟動入口
├── requirements.txt        # 依賴清單
├── src/                    # 核心原始碼
│   ├── __init__.py
│   ├── ui_mainwindow.py    # 由 pyside6-uic 產生
│   ├── mainwindow.ui       # Qt Designer 原始檔（可保留）
│   └── hid_worker.py       # HID 通訊背景 Worker
├── docs/                   # 開發文件
│   └── HID_Firmware_Updater_Guide.md
└── dist/                   # 打包後的輸出目錄
```

---

## 12. 總結

你現在已經學會如何：
- 使用 **Qt Designer** 快速設計 GUI
- 將 `.ui` 轉為 Python 程式碼
- 在 **VSCode** 中開發完整應用
- 整合 **HID** 通訊並使用 `QThread` 避免界面凍結
- 使用 **PyInstaller** 打包成可發行的 `.exe`

這套流程可以推廣到其他類似工具開發，希望對你有幫助！有任何問題歡迎提出討論。