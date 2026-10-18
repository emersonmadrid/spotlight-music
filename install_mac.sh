#!/usr/bin/env bash
set -e

echo "🎵 Instalando Spotlight Music en macOS..."

# Verificar si Homebrew está instalado
if ! command -v brew &>/dev/null; then
    echo "⚠️ Homebrew no está instalado. Instalándolo..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "📦 Instalando mpv y yt-dlp con Homebrew..."
brew install mpv yt-dlp python

echo "📦 Instalando librerías de Python..."
pip3 install -r requirements.txt

# Crear enlace simbólico global
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /usr/local/bin 2>/dev/null || true
if [ -w /usr/local/bin ]; then
    ln -sf "$SCRIPT_DIR/main.py" /usr/local/bin/spotlight-music
else
    sudo ln -sf "$SCRIPT_DIR/main.py" /usr/local/bin/spotlight-music
fi

echo ""
echo "✅ ¡Instalación en macOS completada con éxito!"
echo "👉 Puedes ejecutarlo desde la terminal con: spotlight-music search"
