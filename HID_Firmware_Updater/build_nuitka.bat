@echo off
chcp 65001 >nul
setlocal

REM 檢查是否提供檔名參數
if "%~1"=="" (
    echo [錯誤] 請提供輸出的執行檔名稱！
    echo 範例: %0 HIDFirmwareUpdater
    exit /b 1
)

set EXE_NAME=%~1

echo ========================================================
echo 開始使用 Nuitka 編譯 %EXE_NAME%.exe ...
echo ========================================================
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-disable-console ^
    --output-filename="%EXE_NAME%.exe" ^
    main.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo ✅ 編譯成功！您的執行檔為: %EXE_NAME%.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo ❌ 編譯失敗，請檢查上方的錯誤訊息。
    echo ========================================================
)

endlocal
