@echo off
chcp 65001 >nul
goto :start

:start
setlocal

REM 檢查是否提供檔名參數
if "%~1"=="" (
    echo [錯誤] 請提供要壓縮的執行檔名稱！
    echo 範例: %0 HIDFirmwareUpdater
    exit /b 1
)

set EXE_NAME=%~1
set UPX_PATH=tools\upx.exe

if not exist "%UPX_PATH%" (
    echo [錯誤] 找不到 UPX 執行檔: %UPX_PATH%
    echo 請先下載 UPX 並將 upx.exe 放置於 tools 目錄下。
    exit /b 1
)

set TARGET_EXE=dist\%EXE_NAME%.exe

if not exist "%TARGET_EXE%" (
    if exist "%EXE_NAME%.exe" (
        set TARGET_EXE=%EXE_NAME%.exe
    ) else (
        echo [錯誤] 找不到指定的執行檔: dist\%EXE_NAME%.exe 或 %EXE_NAME%.exe
        exit /b 1
    )
)

echo ========================================================
echo 開始使用 UPX 壓縮 %TARGET_EXE% ...
echo ========================================================
echo.

"%UPX_PATH%" --best "%TARGET_EXE%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo ✅ 壓縮成功！您的執行檔 %TARGET_EXE% 已成功縮小。
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo ❌ 壓縮失敗，請檢查上方的錯誤訊息。
    echo ========================================================
)

endlocal
