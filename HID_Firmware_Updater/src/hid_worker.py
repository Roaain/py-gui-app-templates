# src/hid_worker.py — HID 通訊背景 Worker
import time
import hid
from PySide6.QtCore import QObject, Signal


class HIDWorker(QObject):
    """背景執行緒 Worker，負責 HID 設備連線與韌體更新。

    Signals:
        log(str):              即時日誌訊息，轉發給 UI 顯示。
        progress(int):         更新進度 0-100。
        finished(bool, str):   完成信號 (成功與否, 訊息)。
    """

    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)

    def __init__(self, vid: str, pid: str, firmware_path: str):
        super().__init__()
        # 支援 '0x' 前綴的十六進位字串
        self.vid = int(vid, 0) if isinstance(vid, str) and vid.startswith('0x') else int(vid)
        self.pid = int(pid, 0) if isinstance(pid, str) and pid.startswith('0x') else int(pid)
        self.firmware_path = firmware_path
        self._is_cancelled = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def cancel(self):
        """由主執行緒呼叫，請求中止更新。"""
        self._is_cancelled = True

    def run(self):
        """Worker 主要執行邏輯，由 QThread.started 信號觸發。"""
        device = None
        try:
            # --- 開啟設備 ---
            self.log.emit(f"正在打開 HID 設備 (VID=0x{self.vid:04X}, PID=0x{self.pid:04X})...")
            device = hid.device()
            device.open(self.vid, self.pid)

            manufacturer = device.get_manufacturer_string() or "N/A"
            product = device.get_product_string() or "N/A"
            self.log.emit(f"設備已連線：{manufacturer} - {product}")

            # --- 讀取韌體檔案 ---
            self.log.emit(f"正在讀取韌體檔案：{self.firmware_path}")
            with open(self.firmware_path, 'rb') as f:
                firmware = f.read()

            total = len(firmware)
            if total == 0:
                raise ValueError("韌體檔案為空")

            self.log.emit(f"韌體大小：{total} bytes")

            # --- 分塊寫入 ---
            chunk_size = 64
            sent = 0
            for i in range(0, total, chunk_size):
                if self._is_cancelled:
                    self.log.emit("⚠️ 更新已被使用者取消")
                    self.finished.emit(False, "使用者取消")
                    return

                chunk = firmware[i:i + chunk_size]
                # 補齊到 chunk_size（HID report 通常需要固定長度）
                if len(chunk) < chunk_size:
                    chunk = chunk + bytes(chunk_size - len(chunk))

                # 第一個 byte 為 Report ID（此處假設為 0x00）
                report = bytes([0x00]) + chunk
                device.write(report)

                sent += len(chunk)
                pct = int(sent / total * 100)
                self.progress.emit(min(pct, 100))

                # 預留少量延遲，讓設備有時間處理
                time.sleep(0.005)

            self.progress.emit(100)
            self.log.emit("韌體更新完成！")
            self.finished.emit(True, "更新成功")

        except FileNotFoundError:
            self.log.emit(f"錯誤：找不到韌體檔案 '{self.firmware_path}'")
            self.finished.emit(False, "找不到韌體檔案")
        except IOError as e:
            self.log.emit(f"錯誤：HID 設備通訊失敗 — {e}")
            self.finished.emit(False, str(e))
        except Exception as e:
            self.log.emit(f"錯誤：{e}")
            self.finished.emit(False, str(e))
        finally:
            if device is not None:
                try:
                    device.close()
                    self.log.emit("設備已關閉")
                except Exception:
                    pass
