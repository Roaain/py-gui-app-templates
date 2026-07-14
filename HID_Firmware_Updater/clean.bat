@echo off
setlocal

REM Remove PyInstaller directories
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Remove Nuitka directories
if exist "main.build" rmdir /s /q "main.build"
if exist "main.dist" rmdir /s /q "main.dist"
if exist "main.onefile-build" rmdir /s /q "main.onefile-build"

REM Remove .spec files
del /s /q "*.spec" >nul 2>&1

REM Remove Python __pycache__ folders
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Project cleaned successfully!
endlocal
