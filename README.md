# 🎵 Spotlight Music

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/emersonmadrid/spotlight-music/build-releases.yml?branch=main&style=for-the-badge&label=Build%20Status" alt="Build Status">
  <img src="https://img.shields.io/github/v/release/emersonmadrid/spotlight-music?include_prereleases&style=for-the-badge&label=Release" alt="Release">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Python-3.8+-yellow.svg?style=for-the-badge" alt="Python">
</p>

Reproductor de música en segundo plano ultra-ligero y minimalista con buscador flotante estilo **Spotlight / Raycast**, radio continua de YouTube Music, visor de letras en vivo y ecualizador de audio en tiempo real.

Diseñado para consumir menos de **25 MB de memoria RAM** y prácticamente **0% de uso de CPU**.

---

## ⚡ Descarga Directa (Ejecutables Precompilados)

Gracias a nuestro pipeline de integración continua (**GitHub Actions**), cada vez que el código se actualiza se generan automáticamente los ejecutables portables oficiales listos para usar:

| Sistema Operativo | Archivo de Descarga | Instrucción |
| :--- | :--- | :--- |
| 🪟 **Windows (10/11 x64)** | [📥 **SpotlightMusic-Windows-x64.zip**](https://github.com/emersonmadrid/spotlight-music/releases/download/rolling/SpotlightMusic-Windows-x64.zip) | Descomprimir y abrir `SpotlightMusic.exe` |
| 🐧 **Linux (x86_64)** | [📥 **SpotlightMusic-Linux-x64.tar.gz**](https://github.com/emersonmadrid/spotlight-music/releases/download/rolling/SpotlightMusic-Linux-x64.tar.gz) | Descomprimir y ejecutar `./spotlight-music` |
| 🍏 **macOS (Intel/Apple Silicon)** | [📥 **SpotlightMusic-macOS-x64.tar.gz**](https://github.com/emersonmadrid/spotlight-music/releases/download/rolling/SpotlightMusic-macOS-x64.tar.gz) | Descomprimir y ejecutar `./spotlight-music` |

> *También puedes ver todas las versiones y notas de publicación en [GitHub Releases](https://github.com/emersonmadrid/spotlight-music/releases).*

---

## ✨ Características Principales

* 🔍 **Mini-Player / Buscador Spotlight:** Presiona tu atajo de teclado (`Super + M`) para abrir la tarjeta flotante, escribir cualquier canción o artista y reproducir al instante.
* 📻 **Mix Continuo / Radio Automática:** Al reproducir cualquier canción, se genera una cola continua de 30 temas relacionados para que la música nunca se detenga.
* 🎤 **Visor de Letras (Lyrics):** Ventana flotante oscura con tipografía centrada conectada a *LRCLIB* y *lyrics.ovh*.
* 🔊 **Normalización de Volumen Automática:** Integra el filtro `dynaudnorm` de FFmpeg en `mpv` para evitar variaciones bruscas de volumen entre canciones.
* 🎚️ **Ecualizador en Tiempo Real:** Perfiles instantáneos para *Bass Boost (Graves)*, *Voz Clara*, *Brillo/Agudos* y *Modo Plano*.
* ☕ **Presets de Concentración:** Botones directos para Lo-Fi Beats, Música Clásica, Jazz Instrumental y Pomodoro de 25 minutos.
* 🌐 **Multiplataforma Nativo:** Compatible con Linux, Windows y macOS.

---

## 📦 Instalación Rápida con Scripts Automáticos

Si prefieres instalarlo desde el código fuente con sus dependencias:

### 🐧 En Linux (Fedora, Ubuntu, Debian, Arch)
```bash
git clone https://github.com/emersonmadrid/spotlight-music.git
cd spotlight-music
./install.sh
```

### 🪟 En Windows (1 Clic)
1. Descarga o clona este repositorio:
   ```cmd
   git clone https://github.com/emersonmadrid/spotlight-music.git
   cd spotlight-music
   ```
2. Haz doble clic en **`install_windows.bat`**.

### 🍏 En macOS (Mac)
```bash
git clone https://github.com/emersonmadrid/spotlight-music.git
cd spotlight-music
./install_mac.sh
```

### 🐍 O instalación universal con Python
```bash
pip install .
```

---

## 💻 Control desde Terminal (CLI)

Puedes controlar todo desde tu consola:

```bash
spotlight-music search              # Abre la tarjeta flotante Spotlight
spotlight-music play "daft punk"    # Reproduce un tema directamente
spotlight-music pause               # Conmuta Play / Pausa
spotlight-music next                # Pasa a la siguiente canción del mix
spotlight-music prev                # Vuelve a la canción anterior
spotlight-music stop                # Detiene la música
spotlight-music lyrics              # Abre la ventana de la letra
spotlight-music bass                # Activa refuerzo de graves (Bass Boost)
spotlight-music voz                 # Claridad vocal
spotlight-music plano               # Sonido plano de estudio
spotlight-music like                # Guarda el tema actual en favoritos
spotlight-music favs                # Reproduce tu lista de favoritas en aleatorio
```

---

## ⌨️ Atajo Global Recomendado

En la configuración de atajos de tu sistema operativo (ej. GNOME Settings ➔ Teclado ➔ Atajos personalizados):
* **Nombre:** `Spotlight Music`
* **Comando:** `spotlight-music search` *(o `python3 /ruta/a/main.py search`)*
* **Atajo:** `Super + M`

---

## ⚖️ Aviso Legal, Derechos de Autor y Herramientas de Terceros

Este proyecto se ha desarrollado bajo un estricto compromiso con la legalidad, el código abierto y el respeto a la propiedad intelectual:

1. **Sin Alojamiento de Contenido:** Spotlight Music **no almacena, no descarga, no retransmite ni aloja archivos de audio o video protegidos por derechos de autor**. 
2. **Reproducción Local y Efímera:** Todo el flujo se procesa localmente en la máquina del usuario final mediante herramientas de código abierto independientes (`mpv` y `yt-dlp`).
3. **Reconocimiento de Licencias de Terceros:**
   * **[mpv](https://mpv.io/):** Licencia GPLv2 / LGPLv2.1.
   * **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Licencia The Unlicense.
   * **[LRCLIB](https://lrclib.net/) & [lyrics.ovh](https://lyrics.ovh/):** APIs comunitarias bajo principios de Fair Use informativo.
4. **Marcas Registradas:** Todas las marcas, nombres de artistas, canciones y logotipos pertenecen a sus respectivos propietarios (Google LLC, discográficas y creadores).

Para más detalles legales, consulta el documento completo [DISCLAIMER.md](DISCLAIMER.md).

---

## 📄 Licencia

Código abierto bajo licencia [MIT](LICENSE). Libre para modificar, compartir y adaptar comercial o personalmente.
