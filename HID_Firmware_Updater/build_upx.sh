#!/bin/bash

# 檢查是否提供檔名參數
if [ -z "$1" ]; then
    echo "[錯誤] 請提供要壓縮的執行檔名稱！"
    echo "範例: ./build_upx.sh HIDFirmwareUpdater"
    exit 1
fi

EXE_NAME="$1"
UPX_PATH="tools/upx.exe"

# 判斷系統可用的 UPX 執行檔
if [ -f "$UPX_PATH" ]; then
    UPX_CMD="$UPX_PATH"
elif command -v upx >/dev/null 2>&1; then
    UPX_CMD="upx"
else
    echo "[錯誤] 找不到 UPX 執行檔！"
    echo "請將 upx.exe 放置於 tools 目錄下，或安裝 upx 到系統環境變數中。"
    exit 1
fi

TARGET_FILE="dist/${EXE_NAME}.exe"
if [ ! -f "$TARGET_FILE" ]; then
    TARGET_FILE="dist/${EXE_NAME}"
    if [ ! -f "$TARGET_FILE" ]; then
        TARGET_FILE="${EXE_NAME}.exe"
        if [ ! -f "$TARGET_FILE" ]; then
            if [ -f "${EXE_NAME}" ]; then
                TARGET_FILE="${EXE_NAME}"
            else
                echo "[錯誤] 找不到指定的執行檔: dist/${EXE_NAME}.exe 或 ${EXE_NAME}.exe"
                exit 1
            fi
        fi
    fi
fi

echo "========================================================"
echo "開始使用 UPX 壓縮 ${TARGET_FILE} ..."
echo "========================================================"
echo ""

"$UPX_CMD" --best "$TARGET_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================"
    echo "✅ 壓縮成功！您的執行檔 ${TARGET_FILE} 已成功縮小。"
    echo "========================================================"
else
    echo ""
    echo "========================================================"
    echo "❌ 壓縮失敗，請檢查上方的錯誤訊息。"
    echo "========================================================"
fi
