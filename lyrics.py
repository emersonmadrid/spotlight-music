"""
Módulo de búsqueda y visualización de letras de canciones (LRCLIB + lyrics.ovh).
"""

import sys
import re
import json
import urllib.request
import urllib.parse
from player import get_property, es_titulo_valido


def get_current_track_info():
    """Extrae el artista y nombre de canción limpios desde mpv."""
    raw_title = get_property("media-title") or ""
    metadata = get_property("metadata") or {}

    artist = metadata.get("artist") or metadata.get("ARTIST") or ""
    track = metadata.get("title") or metadata.get("TITLE") or ""

    if not artist and " - " in raw_title:
        parts = raw_title.split(" - ", 1)
        artist = parts[0].strip()
        track = parts[1].strip()
    elif not track:
        track = raw_title

    # Limpieza de sufijos comunes de YouTube
    track = re.sub(r'\(.*?(Audio|Video|Oficial|HQ|HD|Remaster|Letra).*?\)', '', track, flags=re.I)
    track = re.sub(r'\[.*?(Audio|Video|Oficial|HQ|HD|Remaster|Letra).*?\]', '', track, flags=re.I)
    track = re.sub(r'[💔💿🔥✨🎵▶️|]', '', track).strip()

    return artist.strip(), track.strip(), raw_title


def fetch_lyrics(artist, track):
    """Consulta la letra en LRCLIB (primario) y lyrics.ovh (respaldo)."""
    if not track:
        return "⚠️ No hay ninguna canción reproduciéndose actualmente."

    # 1. LRCLIB (máxima calidad tipográfica y sincronización)
    try:
        q = urllib.parse.quote(f"{artist} {track}".strip())
        url = f"https://lrclib.net/api/search?q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "SpotlightMusic/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            items = json.loads(resp.read().decode('utf-8'))
            if items and len(items) > 0:
                l = items[0].get("plainLyrics")
                if not l and items[0].get("syncedLyrics"):
                    l = re.sub(r'\[\d+:\d+\.\d+\]\s*', '', items[0]["syncedLyrics"])
                if l:
                    return l.strip()
    except Exception:
        pass

    # 2. Respaldo: lyrics.ovh
    try:
        a_clean = re.sub(r'[^\w\s]', '', artist).strip()
        t_clean = re.sub(r'[^\w\s]', '', track).strip()
        url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(a_clean)}/{urllib.parse.quote(t_clean)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data.get("lyrics"):
                return data["lyrics"].strip()
    except Exception:
        pass

    return f"❌ No se encontró la letra de:\n'{artist} - {track}'\n\nPuede ser una versión instrumental o no estar disponible en la base de datos."


def show_lyrics_window():
    """Muestra la letra en una ventana flotante oscura y minimalista."""
    artist, track, _ = get_current_track_info()
    lyrics = fetch_lyrics(artist, track)

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk

        win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        win.set_decorated(False)
        win.set_app_paintable(True)
        win.set_default_size(460, 560)
        win.set_position(Gtk.WindowPosition.CENTER)
        win.set_keep_above(True)

        screen = win.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            win.set_visual(visual)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        window { background-color: transparent; }
        .lyrics-card {
            background-color: #121217;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 20px;
            padding: 20px 24px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
        }
        .header-title { color: #ffffff; font-size: 16px; font-weight: bold; }
        .header-artist { color: #9ba1b5; font-size: 13px; }
        button.close-btn {
            background-image: none;
            background-color: #22232e;
            color: #b0b4c4;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 4px 10px;
            font-size: 12px;
            font-weight: bold;
        }
        button.close-btn:hover { background-color: #313344; color: #ffffff; }
        textview, textview text {
            background-color: transparent;
            color: #dcdfe8;
            font-size: 15px;
        }
        scrollbar slider { background-color: rgba(255, 255, 255, 0.15); border-radius: 6px; min-width: 5px; }
        scrollbar trough { background-color: transparent; }
        .hint-label { color: #5d6175; font-size: 11px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        card.get_style_context().add_class("lyrics-card")
        win.add(card)

        # Encabezado
        header_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        lbl_title = Gtk.Label(label=track or "Canción desconocida")
        lbl_title.get_style_context().add_class("header-title")
        lbl_title.set_xalign(0)
        lbl_title.set_ellipsize(3)
        title_box.pack_start(lbl_title, False, False, 0)

        if artist:
            lbl_art = Gtk.Label(label=artist)
            lbl_art.get_style_context().add_class("header-artist")
            lbl_art.set_xalign(0)
            lbl_art.set_ellipsize(3)
            title_box.pack_start(lbl_art, False, False, 0)

        header_content.pack_start(title_box, True, True, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.get_style_context().add_class("close-btn")
        btn_close.connect("clicked", lambda _: win.destroy())
        header_content.pack_end(btn_close, False, False, 0)

        card.pack_start(header_content, False, False, 0)
        card.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # Vista de letra centrada
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_justification(Gtk.Justification.CENTER)
        textview.set_pixels_below_lines(8)
        textview.set_left_margin(12)
        textview.set_right_margin(12)

        buf = textview.get_buffer()
        buf.set_text(lyrics)
        scrolled.add(textview)
        card.pack_start(scrolled, True, True, 0)

        lbl_hint = Gtk.Label(label="Presiona Esc o ✕ para cerrar")
        lbl_hint.get_style_context().add_class("hint-label")
        card.pack_end(lbl_hint, False, False, 0)

        win.connect("key-press-event", lambda _w, e: win.destroy() if e.keyval == Gdk.KEY_Escape else False)
        win.connect("destroy", Gtk.main_quit)

        win.show_all()
        Gtk.main()
    except Exception:
        # Fallback a consola si no hay servidor gráfico GTK
        print(f"\n🎵 {track} - {artist}\n{'=' * 40}")
        print(lyrics)
        print("=" * 40 + "\n")
