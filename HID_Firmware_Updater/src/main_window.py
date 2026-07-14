# src/main_window.py — 主視窗類別
import hid
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit,
    QFileDialog, QGroupBox,
)
from PySide6.QtCore import QThread
from PySide6.QtGui import QFont, QTextCursor

from src.hid_worker import HIDWorker


class MainWindow(QMainWindow):
    """主視窗：提供 VID/PID 輸入、設備連線測試、韌體更新與日誌顯示。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HID 韌體更新工具")
        self.resize(560, 480)

        self._thread: QThread | None = None
        self._worker: HIDWorker | None = None

        self._init_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI 建構
    # ------------------------------------------------------------------
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # --- 設備設定群組 ---
        device_group = QGroupBox("設備設定")
        device_layout = QHBoxLayout(device_group)

        device_layout.addWidget(QLabel("VID:"))
        self.lineEdit_vid = QLineEdit("0x0835")
        self.lineEdit_vid.setFixedWidth(90)
        device_layout.addWidget(self.lineEdit_vid)

        device_layout.addWidget(QLabel("PID:"))
        self.lineEdit_pid = QLineEdit("0x2a80")
        self.lineEdit_pid.setFixedWidth(90)
        device_layout.addWidget(self.lineEdit_pid)

        self.btn_connect = QPushButton("測試連線")
        device_layout.addWidget(self.btn_connect)

        self.btn_enumerate = QPushButton("枚舉設備")
        device_layout.addWidget(self.btn_enumerate)

        device_layout.addStretch()
        root_layout.addWidget(device_group)

        # --- 韌體更新群組 ---
        update_group = QGroupBox("韌體更新")
        update_layout = QVBoxLayout(update_group)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("韌體檔案:"))
        self.lineEdit_firmware = QLineEdit()
        self.lineEdit_firmware.setPlaceholderText("請選擇 .bin 韌體檔案…")
        self.lineEdit_firmware.setReadOnly(True)
        file_row.addWidget(self.lineEdit_firmware)
        self.btn_browse = QPushButton("瀏覽…")
        file_row.addWidget(self.btn_browse)
        update_layout.addLayout(file_row)

        btn_row = QHBoxLayout()
        self.btn_update = QPushButton("開始更新")
        self.btn_update.setEnabled(False)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        btn_row.addWidget(self.btn_update)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        update_layout.addLayout(btn_row)

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        update_layout.addWidget(self.progressBar)

        root_layout.addWidget(update_group)

        # --- 日誌群組 ---
        log_group = QGroupBox("日誌")
        log_layout = QVBoxLayout(log_group)
        self.textEdit_log = QTextEdit()
        self.textEdit_log.setReadOnly(True)
        self.textEdit_log.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.textEdit_log)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        self.btn_clear_log = QPushButton("清除日誌")
        clear_row.addWidget(self.btn_clear_log)
        log_layout.addLayout(clear_row)

        root_layout.addWidget(log_group, stretch=1)

    # ------------------------------------------------------------------
    # 信號連接
    # ------------------------------------------------------------------
    def _connect_signals(self):
        self.btn_connect.clicked.connect(self._on_connect)
        self.btn_enumerate.clicked.connect(self._on_enumerate)
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_update.clicked.connect(self._on_update)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_clear_log.clicked.connect(self.textEdit_log.clear)

    # ------------------------------------------------------------------
    # 事件處理
    # ------------------------------------------------------------------
    def _log(self, msg: str):
        """將訊息追加到日誌並自動捲動至底部。"""
        self.textEdit_log.append(msg)
        self.textEdit_log.moveCursor(QTextCursor.MoveOperation.End)

    def _parse_vid_pid(self) -> tuple[int, int] | None:
        """解析 VID / PID 文字欄位，失敗時回傳 None 並記錄日誌。"""
        vid_text = self.lineEdit_vid.text().strip()
        pid_text = self.lineEdit_pid.text().strip()
        if not vid_text or not pid_text:
            self._log("⚠️ 請輸入 VID 和 PID")
            return None
        try:
            vid = int(vid_text, 0)
            pid = int(pid_text, 0)
            return vid, pid
        except ValueError:
            self._log("⚠️ VID / PID 格式不正確，請使用十進位或 0x 開頭的十六進位")
            return None

    # --- 枚舉設備 ---
    def _on_enumerate(self):
        self._log("── 枚舉 HID 設備 ──")
        devices = hid.enumerate()
        if not devices:
            self._log("未偵測到任何 HID 設備")
            return
        for d in devices:
            vid = d.get('vendor_id', 0)
            pid = d.get('product_id', 0)
            product = d.get('product_string', '') or ''
            manufacturer = d.get('manufacturer_string', '') or ''
            self._log(
                f"  VID=0x{vid:04X}  PID=0x{pid:04X}  "
                f"{manufacturer} — {product}"
            )
        self._log(f"共 {len(devices)} 個介面")

    # --- 測試連線 ---
    def _on_connect(self):
        result = self._parse_vid_pid()
        if result is None:
            return
        vid, pid = result
        self._log(f"測試連線 VID=0x{vid:04X}, PID=0x{pid:04X} ...")
        try:
            device = hid.device()
            device.open(vid, pid)
            manufacturer = device.get_manufacturer_string() or "N/A"
            product = device.get_product_string() or "N/A"
            self._log(f"✅ 連線成功：{manufacturer} — {product}")
            device.close()
        except Exception as e:
            self._log(f"❌ 連線失敗：{e}")

    # --- 選擇韌體檔案 ---
    def _on_browse(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "選擇韌體檔案", "",
            "Bin Files (*.bin);;All Files (*)",
        )
        if fname:
            self.lineEdit_firmware.setText(fname)
            self.btn_update.setEnabled(True)
            self._log(f"已選擇韌體：{fname}")

    # --- 開始更新 ---
    def _on_update(self):
        result = self._parse_vid_pid()
        if result is None:
            return
        vid, pid = result

        firmware_path = self.lineEdit_firmware.text().strip()
        if not firmware_path:
            self._log("⚠️ 請先選擇韌體檔案")
            return

        # 鎖定 UI
        self._set_updating_ui(True)
        self.progressBar.setValue(0)
        self._log("── 開始韌體更新 ──")

        # 建立 Worker 與 QThread
        self._thread = QThread()
        self._worker = HIDWorker(
            vid=f"0x{vid:04X}",
            pid=f"0x{pid:04X}",
            firmware_path=firmware_path,
        )
        self._worker.moveToThread(self._thread)

        # 連接信號
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self.progressBar.setValue)
        self._worker.finished.connect(self._on_update_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    # --- 取消更新 ---
    def _on_cancel(self):
        if self._worker is not None:
            self._worker.cancel()
            self._log("正在取消更新…")

    # --- 更新完成回呼 ---
    def _on_update_finished(self, success: bool, msg: str):
        self._set_updating_ui(False)
        if success:
            self._log(f"✅ {msg}")
        else:
            self._log(f"❌ 失敗：{msg}")
        self._thread = None
        self._worker = None

    # ------------------------------------------------------------------
    # 輔助
    # ------------------------------------------------------------------
    def _set_updating_ui(self, updating: bool):
        """更新進行中時鎖定/解鎖相關按鈕。"""
        self.btn_update.setEnabled(not updating)
        self.btn_connect.setEnabled(not updating)
        self.btn_enumerate.setEnabled(not updating)
        self.btn_browse.setEnabled(not updating)
        self.btn_cancel.setEnabled(updating)
        self.lineEdit_vid.setEnabled(not updating)
        self.lineEdit_pid.setEnabled(not updating)
