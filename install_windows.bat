@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo ====================================================
echo 🎵 Spotlight Music para Windows
echo ====================================================

if exist "%APP_DIR%SpotlightMusic.exe" goto launch_compiled

REM Entorno con Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro SpotlightMusic.exe ni Python.
    echo Por favor descarga SpotlightMusic-Windows-x64.zip desde GitHub Releases.
    pause
    exit /b 1
)

pip install -r requirements.txt
start "" pythonw.exe "%APP_DIR%main.py"
exit /b 0

:launch_compiled
echo [OK] Ejecutable compilado detectado.
echo Creando acceso directo en el Escritorio...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Spotlight Music.lnk'); $s.TargetPath = (Join-Path $env:APP_DIR 'SpotlightMusic.exe'); $s.WorkingDirectory = $env:APP_DIR; $s.Save()" >nul 2>nul

echo 🚀 Iniciando Spotlight Music...
start "" "%APP_DIR%SpotlightMusic.exe"
exit /b 0
