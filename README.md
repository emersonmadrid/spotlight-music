# 🎵 Spotlight Music

Reproductor de música en segundo plano, ultra-ligero y minimalista, con buscador flotante estilo **Spotlight / Raycast**, radio continua de YouTube Music, visor de letras en tiempo real y ecualizador de audio.

Diseñado para consumir menos de **25 MB de memoria RAM** y prácticamente **0% de uso de CPU**.

---

## ✨ Características Principales

* 🔍 **Mini-Player / Buscador Spotlight:** Presiona tu atajo de teclado o abre la ventana para buscar canciones, ver opciones en vivo y reproducir con un solo clic o `Enter`.
* 📻 **Mix Continuo / Radio Automática:** Al reproducir una canción, se genera una cola continua de 30 temas relacionados para que la música nunca se corte.
* 🎤 **Visor de Letras (Lyrics):** Ventana flotante oscura con tipografía centrada conectada a *LRCLIB* y *lyrics.ovh*.
* 🔊 **Normalización de Volumen Automática:** Integra `dynaudnorm` de FFmpeg en `mpv` para evitar cambios bruscos de volumen entre canciones.
* 🎚️ **Ecualizador en Tiempo Real:** Perfiles rápidos para *Bass Boost (Graves)*, *Voz Clara*, *Brillo/Agudos* y *Plano*.
* ☕ **Presets de Concentración:** Botones directos para Lo-Fi Beats, Música Clásica, Jazz Instrumental y Pomodoro de 25 minutos.
* 🌐 **Multiplataforma:** Compatible con Linux (Fedora, Ubuntu, Arch, etc.), Windows y macOS.

---

## 🚀 Requisitos Previos

Solo necesitas tener instalados en tu sistema:
1. **Python 3.8+**
2. **mpv**: Reproductor de medios ultra-ligero.
3. **yt-dlp**: Extractor de streams y audio de alta fidelidad.

---

## 🐧 Instalación en Linux

### Fedora / RHEL
```bash
sudo dnf install mpv yt-dlp python3-gobject gtk3
```

### Ubuntu / Debian / Pop!_OS
```bash
sudo apt install mpv yt-dlp python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Arch Linux / Manjaro
```bash
sudo pacman -S mpv yt-dlp python-gobject gtk3
```

---

## 🪟 Instalación en Windows

1. Clona o descarga esta carpeta.
2. Descarga `mpv` y `yt-dlp` (o instálalos con `winget`):
   ```cmd
   winget install mpv.net
   winget install yt-dlp
   ```
3. Instala los requisitos de Python:
   ```cmd
   pip install -r requirements.txt
   ```
4. Ejecuta:
   ```cmd
   python main.py
   ```

---

## 💻 Uso desde la Terminal (CLI)

Puedes controlar todo desde tu consola o terminal favorita:

```bash
# Iniciar la interfaz flotante (Spotlight)
python main.py search

# Reproducir directamente cualquier tema o artista
python main.py play "daft punk get lucky"
python main.py play "alejandro sanz"

# Controles de reproducción
python main.py pause        # Conmuta Play / Pausa
python main.py next         # Salta a la siguiente canción del mix
python main.py prev         # Vuelve a la canción anterior
python main.py stop         # Detiene la música

# Ver la letra de la canción sonando
python main.py lyrics

# Perfiles de ecualizador
python main.py bass         # Refuerzo de bajos (Bass Boost)
python main.py voz          # Claridad vocal
python main.py brillo       # Realce acústico y agudos
python main.py plano        # Sonido plano de estudio

# Favoritas
python main.py like         # Guarda el tema actual en favoritos
python main.py favs         # Reproduce tu lista de favoritas en aleatorio
```

---

## ⌨️ Atajo Global Recomendado

En tu configuración de teclado del sistema (ej. GNOME Settings ➔ Teclado ➔ Atajos personalizados):
* **Nombre:** `Spotlight Music`
* **Comando:** `/usr/bin/python3 /ruta/al/proyecto/main.py search`
* **Atajo:** `Super + M`

---

## 📄 Licencia

Código abierto bajo licencia MIT. Libre para modificar, compartir y adaptar.
