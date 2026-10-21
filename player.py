"""
Módulo de control del reproductor mpv mediante IPC (Multiplataforma).
Soporta Linux/macOS (UNIX domain socket) y Windows (Named Pipe).
"""

import os
import sys
import json
import socket
import subprocess
import re
import time

if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    SOCKET_PATH = r"\\.\pipe\mpvsocket"
    FAVS_FILE = os.path.expanduser(r"~\.musica_favoritas.txt")
    HISTORIAL_FILE = os.path.expanduser(r"~\.musica_historial.txt")
else:
    SOCKET_PATH = "/tmp/mpvsocket"
    FAVS_FILE = os.path.expanduser("~/.musica_favoritas.txt")
    HISTORIAL_FILE = os.path.expanduser("~/.musica_historial.txt")


def send_mpv_command(command_list):
    """Envía un comando JSON a la instancia de mpv mediante su socket/pipe IPC."""
    payload = json.dumps({"command": command_list}) + "\n"

    if IS_WINDOWS:
        try:
            with open(SOCKET_PATH, "r+b", buffering=0) as pipe:
                pipe.write(payload.encode("utf-8"))
                response = pipe.readline().decode("utf-8")
                return json.loads(response)
        except Exception:
            return None
    else:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(SOCKET_PATH)
            s.sendall(payload.encode("utf-8"))
            resp_bytes = s.recv(4096)
            s.close()
            return json.loads(resp_bytes.decode("utf-8"))
        except Exception:
            return None


def get_property(prop_name):
    """Lee una propiedad de mpv."""
    res = send_mpv_command(["get_property", prop_name])
    if res and "data" in res:
        return res["data"]
    return None


def set_property(prop_name, value):
    """Establece una propiedad en mpv."""
    return send_mpv_command(["set_property", prop_name, value])


def es_titulo_valido(t):
    """Verifica si el título es el nombre real y no una URL o ID temporal de YouTube."""
    if not t:
        return False
    s = str(t).strip()
    if (s.startswith("watch?v=") or s.startswith("ytdl://") or s.startswith("ytsearch") or
        s.startswith("http://") or s.startswith("https://") or s.startswith("ytdl:")):
        return False
    if len(s) == 11 and " " not in s:
        return False
    return True


def get_status():
    """Devuelve (título, en_pausa, está_activo)."""
    title = get_property("media-title")
    paused = get_property("pause") or False
    activo = title is not None
    return title, paused, activo


def get_playback_time():
    """Devuelve (tiempo_actual_formateado, duracion_formateada)."""
    pos = get_property("time-pos")
    dur = get_property("duration")
    if pos is not None and dur is not None:
        m_pos, s_pos = divmod(int(pos), 60)
        m_dur, s_dur = divmod(int(dur), 60)
        return f"{m_pos:02d}:{s_pos:02d}", f"{m_dur:02d}:{s_dur:02d}"
    elif pos is not None:
        m_pos, s_pos = divmod(int(pos), 60)
        return f"{m_pos:02d}:{s_pos:02d}", "--:--"
    return None, None


def get_mpv_path():
    """Localiza el binario de mpv: primero en la carpeta de la app, luego en PATH."""
    app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
    if IS_WINDOWS:
        candidate = os.path.join(app_dir, "mpv.exe")
        if os.path.exists(candidate):
            return candidate
    else:
        candidate = os.path.join(app_dir, "mpv")
        if os.path.exists(candidate):
            return candidate
    return "mpv"


def get_ytdlp_path():
    """Localiza el binario de yt-dlp: primero en la carpeta de la app, luego en PATH."""
    app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
    if IS_WINDOWS:
        candidate = os.path.join(app_dir, "yt-dlp.exe")
        if os.path.exists(candidate):
            return candidate
    else:
        candidate = os.path.join(app_dir, "yt-dlp")
        if os.path.exists(candidate):
            return candidate
    return "yt-dlp"


def play(query):
    """Inicia la reproducción de una consulta o enlace."""
    if not query:
        return False

    # Detener reproducción previa
    stop()
    time.sleep(0.3)

    # Limpiar socket previo en Linux
    if not IS_WINDOWS and os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except Exception:
            pass

    # Construir URL o búsqueda de YouTube Mix continuo
    regex = r'(youtu\.be/|[?&]v=)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, query)
    if match:
        vid = match.group(2)
        target = f"https://www.youtube.com/watch?v={vid}&list=RD{vid}"
    elif query.startswith("http://") or query.startswith("https://"):
        target = query
    else:
        target = f"ytdl://ytsearch25:{query} audio"

    mpv_bin = get_mpv_path()
    log_file = os.path.join(os.environ.get("TEMP", os.environ.get("TMP", ".")), "spotlight_mpv.log") if IS_WINDOWS else "/tmp/spotlight_mpv.log"
    cmd = [
        mpv_bin,
        "--no-video",
        "--volume=100",
        "--audio-exclusive=no",
        "--ao=wasapi,openal,",
        "--ytdl-raw-options=yes-playlist=,playlist-end=30,extractor-args=youtube:player_client=android",
        f"--input-ipc-server={SOCKET_PATH}",
        f"--log-file={log_file}",
        target
    ]

    # Preparar entorno asegurando que yt-dlp local sea visible
    app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
    env = os.environ.copy()
    env["PATH"] = app_dir + os.pathsep + env.get("PATH", "")

    # Iniciar mpv en segundo plano desacoplado
    try:
        if IS_WINDOWS:
            creation_flags = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
                env=env
            )
        elif IS_LINUX and os.path.exists("/usr/bin/systemd-run"):
            # En Linux podemos delegar a systemd si está disponible, o correr en sesión nueva
            subprocess.run(["systemctl", "--user", "reset-failed", "bg-musica"], stderr=subprocess.DEVNULL)
            subprocess.Popen(
                ["systemd-run", "--user", "--unit=bg-musica"] + cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
        else:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=env
            )
    except FileNotFoundError:
        print("❌ Error: 'mpv' no está instalado o no se encuentra en el PATH del sistema.")
        if IS_WINDOWS:
            print("👉 En Windows puedes instalarlo fácilmente ejecutando: winget install mpv.net")
        elif IS_LINUX:
            print("👉 En Linux puedes instalarlo con: sudo apt install mpv / sudo dnf install mpv")
        return False

    return True


def pause():
    """Conmuta entre pausa y reproducción."""
    return send_mpv_command(["cycle", "pause"])


def next_track():
    """Salta a la siguiente canción de la cola continua."""
    return send_mpv_command(["playlist-next"])


def prev_track():
    """Regresa a la canción anterior."""
    return send_mpv_command(["playlist-prev"])


def stop():
    """Detiene la música por completo."""
    if IS_LINUX:
        subprocess.run(["systemctl", "--user", "stop", "bg-musica"], stderr=subprocess.DEVNULL)
    send_mpv_command(["quit"])
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/IM", "mpv.exe"], stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["pkill", "-f", SOCKET_PATH], stderr=subprocess.DEVNULL)


def set_volume(level):
    """Ajusta el volumen (0 a 100)."""
    return set_property("volume", int(level))


def set_equalizer(profile):
    """Ajusta los filtros de ecualización en tiempo real."""
    profiles = {
        "bass": "lavfi=[equalizer=f=64:t=q:w=1:g=8]",
        "voz": "lavfi=[equalizer=f=1000:t=q:w=1:g=5]",
        "brillo": "lavfi=[equalizer=f=8000:t=q:w=1:g=6]",
        "plano": "",
    }
    filter_val = profiles.get(profile, "")
    res = set_property("af", filter_val)
    return res is not None and res.get("error") == "success"


def save_favorite():
    """Guarda la canción que suena actualmente en la lista de favoritos."""
    title = get_property("media-title")
    path = get_property("path")
    if not path and not title:
        return False, "No hay música sonando"

    target_entry = path or title
    if os.path.exists(FAVS_FILE):
        with open(FAVS_FILE, "r", encoding="utf-8") as f:
            if target_entry in f.read():
                return True, f"Ya estaba en favoritos: {title or target_entry}"

    with open(FAVS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{target_entry} # {title or 'Sin título'} [{time.strftime('%Y-%m-%d')}]\n")

    return True, f"Guardada en favoritos: {title or target_entry}"


def play_favorites():
    """Reproduce la lista de favoritos en modo aleatorio."""
    if not os.path.exists(FAVS_FILE) or os.path.getsize(FAVS_FILE) == 0:
        return False, "Aún no tienes canciones favoritas guardadas"

    entries = []
    with open(FAVS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            item = line.split("#")[0].strip()
            if item:
                entries.append(item)

    if not entries:
        return False, "No se encontraron temas en favoritos"

    import random
    random.shuffle(entries)
    return play(entries[0])

    temp_playlist = "/tmp/mpv_favoritas.m3u" if not IS_WINDOWS else os.path.expanduser(r"~\mpv_favs.m3u")
    with open(temp_playlist, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + "\n")

    stop()
    mpv_bin = get_mpv_path()
    log_file = os.path.join(os.environ.get("TEMP", os.environ.get("TMP", ".")), "spotlight_mpv.log") if IS_WINDOWS else "/tmp/spotlight_mpv.log"
    cmd = [
        mpv_bin,
        "--no-video",
        "--volume=85",
        "--audio-exclusive=no",
        "--ao=wasapi,openal,",
        "--shuffle",
        "--af=dynaudnorm",
        "--ytdl-raw-options=yes-playlist=,playlist-end=30,extractor-args=youtube:player_client=android",
        f"--input-ipc-server={SOCKET_PATH}",
        f"--log-file={log_file}",
        f"--playlist={temp_playlist}"
    ]
    app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
    env = os.environ.copy()
    env["PATH"] = app_dir + os.pathsep + env.get("PATH", "")

    if IS_WINDOWS:
        creation_flags = 0x08000000 | 0x00000008
        subprocess.Popen(cmd, creationflags=creation_flags, env=env)
    elif IS_LINUX and os.path.exists("/usr/bin/systemd-run"):
        subprocess.run(["systemctl", "--user", "reset-failed", "bg-musica"], stderr=subprocess.DEVNULL)
        subprocess.Popen(
            ["systemd-run", "--user", "--unit=bg-musica"] + cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=env)

    return True, "Reproduciendo tus canciones favoritas"
