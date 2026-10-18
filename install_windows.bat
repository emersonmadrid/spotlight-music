@echo off
chcp 65001 > nul
echo ====================================================
echo 🎵 Instalador de Spotlight Music para Windows
echo ====================================================

REM 1. Verificar si existe el ejecutable precompilado
if exist "%~dp0SpotlightMusic.exe" (
    echo [OK] Se detectó el ejecutable compilado 'SpotlightMusic.exe'.
    echo No requiere instalar Python ni dependencias adicionales.
    goto check_mpv
)

REM 2. Si no hay .exe, verificar Python para el entorno de desarrollo
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor descarga e instala Python desde https://www.python.org/
    echo o descarga el paquete precompilado SpotlightMusic-Windows-x64.zip desde los Releases.
    pause
    exit /b 1
)

echo.
echo [1/3] Instalando dependencias de Python...
pip install -r requirements.txt

:check_mpv
echo.
echo [2/3] Verificando motor de reproducción de audio (mpv)...
where mpv >nul 2>nul
if %errorlevel% neq 0 (
    echo Instalando mpv mediante winget (gestor oficial de Windows)...
    winget install --id shinchiro.mpv --silent --accept-source-agreements --accept-package-agreements 2>nul || winget install mpv.net 2>nul
) else (
    echo [OK] mpv ya está instalado.
)

echo.
echo [3/3] Creando acceso directo en el Escritorio...
if exist "%~dp0SpotlightMusic.exe" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Spotlight Music.lnk'); $Shortcut.TargetPath = '%~dp0SpotlightMusic.exe'; $Shortcut.Arguments = 'search'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
) else (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Spotlight Music.lnk'); $Shortcut.TargetPath = 'pythonw.exe'; $Shortcut.Arguments = '\"%~dp0main.py\" search'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
)

echo.
echo ====================================================
echo ✅ ¡Instalación completada con éxito en Windows!
echo 👉 Encontrarás el icono "Spotlight Music" en tu Escritorio.
echo ====================================================
pause
