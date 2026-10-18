@echo off
chcp 65001 > nul
echo ====================================================
echo 🎵 Instalador de Spotlight Music para Windows
echo ====================================================

REM Verificar Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor descarga e instala Python desde https://www.python.org/
    pause
    exit /b 1
)

echo.
echo [1/3] Instalando dependencias de Python...
pip install -r requirements.txt

echo.
echo [2/3] Verificando dependencias del sistema (mpv y yt-dlp)...
where mpv >nul 2>nul
if %errorlevel% neq 0 (
    echo Instalando mpv mediante winget...
    winget install --id shinchiro.mpv --silent --accept-source-agreements --accept-package-agreements 2>nul || winget install mpv.net 2>nul
)

where yt-dlp >nul 2>nul
if %errorlevel% neq 0 (
    echo Instalando yt-dlp mediante winget...
    winget install --id yt-dlp.yt-dlp --silent --accept-source-agreements --accept-package-agreements 2>nul || pip install yt-dlp
)

echo.
echo [3/3] Creando acceso directo en el Escritorio...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Spotlight Music.lnk'); $Shortcut.TargetPath = 'pythonw.exe'; $Shortcut.Arguments = '\"%~dp0main.py\" search'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"

echo.
echo ====================================================
echo ✅ ¡Instalación completada con éxito en Windows!
echo 👉 Encontrarás el icono "Spotlight Music" en tu Escritorio.
echo ====================================================
pause
