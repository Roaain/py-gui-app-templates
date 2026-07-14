@echo off
chcp 65001 >nul
goto :start

:start
setlocal

if "%~1"=="" (
    echo [錯誤] 請提供輸出的執行檔名稱！
    echo 範例: %0 HIDFirmwareUpdater
    exit /b 1
)

set EXE_NAME=%~1
set SFX_PATH=tools\7zS.sfx
set SEVEN_Z_PATH=tools\7z.exe

if not exist "%SFX_PATH%" (
    echo [錯誤] 找不到 %SFX_PATH%
    echo 請前往 7-Zip 官網下載 7z Extra 包，將 7zS.sfx 放入 tools 資料夾。
    exit /b 1
)

REM 尋找 7z.exe
set "SZ_CMD="
if exist "%SEVEN_Z_PATH%" (
    set "SZ_CMD=%SEVEN_Z_PATH%"
) else (
    for %%X in (7z.exe) do set "SZ_CMD=%%~dp$PATH:X7z.exe"
    if not defined SZ_CMD (
        if exist "C:\Program Files\7-Zip\7z.exe" (
            set "SZ_CMD=C:\Program Files\7-Zip\7z.exe"
        ) else (
            echo [錯誤] 找不到 7z.exe，請安裝 7-Zip 或將 7z.exe 放入 tools 資料夾。
            exit /b 1
        )
    )
)

echo ========================================================
echo (1/4) 正在使用 PyInstaller 打包 (資料夾模式) ...
echo ========================================================
pyinstaller -y -w -n "%EXE_NAME%" main.py
if %ERRORLEVEL% neq 0 (
    echo [錯誤] PyInstaller 打包失敗。
    exit /b 1
)

echo ========================================================
echo (2/4) 建立 SFX 設定檔 config.txt ...
echo ========================================================
(
    echo ;!@Install@!UTF-8!
    echo Title="%EXE_NAME%"
    echo RunProgram="%EXE_NAME%.exe"
    echo ;!@InstallEnd@!
) > "dist\%EXE_NAME%\config.txt"

echo ========================================================
echo (3/4) 壓縮成 app.7z (LZMA 最高壓縮率) ...
echo ========================================================
if exist "dist\%EXE_NAME%\app.7z" del /f /q "dist\%EXE_NAME%\app.7z"
pushd "dist\%EXE_NAME%"
"%SZ_CMD%" a -mx=9 app.7z * -x!app.7z -x!config.txt
popd

echo ========================================================
echo (4/4) 合併成單一執行檔 ...
echo ========================================================
copy /b "%SFX_PATH%" + "dist\%EXE_NAME%\config.txt" + "dist\%EXE_NAME%\app.7z" "dist\%EXE_NAME%_SFX.exe" >nul

echo.
echo ========================================================
echo ✅ 打包完成！您的自解壓縮執行檔位於: dist\%EXE_NAME%_SFX.exe
echo ========================================================
endlocal
