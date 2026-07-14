#!/bin/bash

if [ -z "$1" ]; then
    echo "[錯誤] 請提供輸出的執行檔名稱！"
    echo "範例: ./build_7z.sh HIDFirmwareUpdater"
    exit 1
fi

EXE_NAME="$1"
SFX_PATH="tools/7zS.sfx"

if [ ! -f "$SFX_PATH" ]; then
    echo "[錯誤] 找不到 ${SFX_PATH}"
    echo "請前往 7-Zip 官網下載 7z Extra 包，將 7zS.sfx 放入 tools 資料夾。"
    exit 1
fi

if command -v 7z >/dev/null 2>&1; then
    SZ_CMD="7z"
elif command -v 7za >/dev/null 2>&1; then
    SZ_CMD="7za"
elif [ -f "tools/7z.exe" ]; then
    SZ_CMD="tools/7z.exe"
else
    echo "[錯誤] 找不到 7z 指令！"
    echo "請安裝 p7zip (Linux) 或確保 7-Zip 在系統環境變數中，或放入 tools 資料夾。"
    exit 1
fi

echo "========================================================"
echo "(1/4) 正在使用 PyInstaller 打包 (資料夾模式) ..."
echo "========================================================"
pyinstaller -y -w -n "${EXE_NAME}" main.py
if [ $? -ne 0 ]; then
    echo "[錯誤] PyInstaller 打包失敗。"
    exit 1
fi

echo "========================================================"
echo "(2/4) 建立 SFX 設定檔 config.txt ..."
echo "========================================================"
cat << EOF > "dist/${EXE_NAME}/config.txt"
;!@Install@!UTF-8!
Title="${EXE_NAME}"
RunProgram="${EXE_NAME}.exe"
;!@InstallEnd@!
EOF

echo "========================================================"
echo "(3/4) 壓縮成 app.7z (LZMA 最高壓縮率) ..."
echo "========================================================"
rm -f "dist/${EXE_NAME}/app.7z"
cd "dist/${EXE_NAME}" || exit 1
"$SZ_CMD" a -mx=9 app.7z * -x!app.7z -x!config.txt
cd ../.. || exit 1

echo "========================================================"
echo "(4/4) 合併成單一執行檔 ..."
echo "========================================================"
cat "$SFX_PATH" "dist/${EXE_NAME}/config.txt" "dist/${EXE_NAME}/app.7z" > "dist/${EXE_NAME}_SFX.exe"
chmod +x "dist/${EXE_NAME}_SFX.exe"

echo ""
echo "========================================================"
echo "✅ 打包完成！您的自解壓縮執行檔位於: dist/${EXE_NAME}_SFX.exe"
echo "========================================================"
