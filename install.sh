#!/usr/bin/env bash
set -e

echo "🎵 Instalando Spotlight Music en Linux..."

# Detectar gestor de paquetes e instalar dependencias del sistema
if command -v dnf &>/dev/null; then
    echo "📦 Detectado Fedora/RHEL. Instalando dependencias con dnf..."
    sudo dnf install -y mpv yt-dlp python3-gobject gtk3
elif command -v apt-get &>/dev/null; then
    echo "📦 Detectado Debian/Ubuntu. Instalando dependencias con apt..."
    sudo apt-get update && sudo apt-get install -y mpv yt-dlp python3-gi python3-gi-cairo gir1.2-gtk-3.0
elif command -v pacman &>/dev/null; then
    echo "📦 Detectado Arch Linux. Instalando dependencias con pacman..."
    sudo pacman -S --noconfirm mpv yt-dlp python-gobject gtk3
fi

# Instalar dependencias de Python si existen
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt 2>/dev/null || true
fi

# Crear directorio de binarios de usuario si no existe
mkdir -p "$HOME/.local/bin"

# Crear lanzador global en ~/.local/bin/spotlight-music
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat <<EOF > "$HOME/.local/bin/spotlight-music"
#!/usr/bin/env bash
python3 "$SCRIPT_DIR/main.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/spotlight-music"

# Crear acceso directo de escritorio
mkdir -p "$HOME/.local/share/applications"
cat <<EOF > "$HOME/.local/share/applications/spotlight-music.desktop"
[Desktop Entry]
Name=Spotlight Music
Comment=Reproductor minimalista en segundo plano
Exec=spotlight-music search
Icon=audio-headphones
Terminal=false
Type=Application
Categories=Audio;Music;Player;
EOF

echo ""
echo "✅ ¡Instalación completada con éxito!"
echo "👉 Puedes ejecutarlo desde la terminal con: spotlight-music search"
echo "👉 O configurar tu atajo de teclado favorito (ej. Super+M) apuntando a: spotlight-music search"
