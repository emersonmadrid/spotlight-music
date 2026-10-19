#!/usr/bin/env python3
"""
Spotlight Music: Reproductor de música en segundo plano ultra-ligero y minimalista.
Multiplataforma (Linux, Windows, macOS).
"""

import os
import sys
import threading
import subprocess
import time

# Configuración para Windows: Conexión híbrida con consola y codificación UTF-8
if sys.platform == "win32":
    try:
        import ctypes
        # Si se ejecutó desde CMD o PowerShell, adjuntar la salida a dicha terminal
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stdout is None:
    class DummyStream:
        def write(self, *args, **kwargs): pass
        def flush(self, *args, **kwargs): pass
        def reconfigure(self, *args, **kwargs): pass
    sys.stdout = DummyStream()

if sys.stderr is None:
    sys.stderr = sys.stdout

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import player
import lyrics

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
except ImportError:
    tk = None


def show_spotlight_player(initial_query=""):
    """Lanza la ventana flotante Spotlight / Raycast."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk, GLib
    except (ImportError, ValueError):
        # Fallback universal nativo (Windows, macOS o Linux sin GTK3)
        show_spotlight_tkinter(initial_query)
        return

    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_decorated(False)
    win.set_app_paintable(True)
    win.set_keep_above(True)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_default_size(480, 160)

    screen = win.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        win.set_visual(visual)

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(b"""
    window { background-color: transparent; }
    .floating-card {
        background-color: #121217;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.7);
    }
    .now-playing-box {
        background-color: #181922;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 10px 14px;
    }
    .track-title { color: #ffffff; font-size: 14px; font-weight: bold; }
    .track-artist { color: #8c92a6; font-size: 12px; }
    button { background-image: none; box-shadow: none; text-shadow: none; }
    button.ctrl-btn {
        background-image: none;
        background-color: #252633;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 6px 11px;
        font-size: 13px;
        font-weight: bold;
    }
    button.ctrl-btn:hover { background-color: #353648; color: #ffffff; }
    entry.spotlight-input {
        background-image: none;
        font-size: 14px;
        padding: 10px 14px;
        border-radius: 12px;
        background-color: #181922;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    entry.spotlight-input:focus { background-color: #1e1f2b; border-color: #3584e4; }
    button.chip-btn {
        background-image: none;
        background-color: #1a1a24;
        color: #b0b4c8;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.09);
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 500;
    }
    button.chip-btn:hover { background-color: #272836; color: #ffffff; }
    treeview {
        background-color: #171822;
        color: #e2e4ee;
        border-radius: 10px;
        padding: 6px;
        font-size: 13px;
    }
    treeview:selected { background-color: #2e3040; color: #ffffff; border-radius: 6px; }
    scrollbar slider { background-color: rgba(255, 255, 255, 0.15); border-radius: 6px; min-width: 5px; }
    scrollbar trough { background-color: transparent; }
    """)
    Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    card.get_style_context().add_class("floating-card")
    win.add(card)

    # 1. Tarjeta superior de canción sonando
    title, paused, activo = player.get_status()
    if activo and title:
        box_np = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_np.get_style_context().add_class("now-playing-box")

        vbox_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_title = Gtk.Label(label=title if player.es_titulo_valido(title) else "⏳ Cargando canción...")
        lbl_title.get_style_context().add_class("track-title")
        lbl_title.set_xalign(0)
        lbl_title.set_ellipsize(3)
        vbox_info.pack_start(lbl_title, False, False, 0)

        lbl_sub = Gtk.Label(label="Reproduciendo ahora" if not paused else "En pausa")
        lbl_sub.get_style_context().add_class("track-artist")
        lbl_sub.set_xalign(0)
        vbox_info.pack_start(lbl_sub, False, False, 0)
        box_np.pack_start(vbox_info, True, True, 0)

        def on_ctrl_click(action, button):
            if action == "pausa":
                player.pause()
                _, p, _ = player.get_status()
                button.set_label("▶" if p else "⏸")
                lbl_sub.set_text("En pausa" if p else "Reproduciendo ahora")
            elif action == "like":
                player.save_favorite()
                button.set_label("💖")
                GLib.timeout_add_seconds(2, lambda: button.set_label("❤️"))
            elif action in ("next", "prev"):
                if action == "next":
                    player.next_track()
                else:
                    player.prev_track()
                lbl_title.set_text("⏳ Cargando canción...")
                def refrescar(intentos=[0]):
                    intentos[0] += 1
                    t, p, _ = player.get_status()
                    if t and player.es_titulo_valido(t):
                        lbl_title.set_text(t)
                        lbl_sub.set_text("Reproduciendo ahora" if not p else "En pausa")
                        return False
                    return intentos[0] < 10
                GLib.timeout_add(600, refrescar)
            elif action == "letra":
                lyrics.show_lyrics_window()

        ctrls = [
            ("⏮", "prev"),
            ("▶" if paused else "⏸", "pausa"),
            ("⏭", "next"),
            ("❤️", "like"),
            ("🎤", "letra"),
        ]
        for icon, act in ctrls:
            b = Gtk.Button(label=icon)
            b.get_style_context().add_class("ctrl-btn")
            b.connect("clicked", lambda btn, a=act: on_ctrl_click(a, btn))
            box_np.pack_start(b, False, False, 0)

        card.pack_start(box_np, False, False, 0)

    # 2. Entrada de búsqueda
    entry = Gtk.Entry()
    entry.get_style_context().add_class("spotlight-input")
    entry.set_placeholder_text("🔍 Escribe cualquier canción, artista o género...")
    if initial_query:
        entry.set_text(initial_query)
    card.pack_start(entry, False, False, 0)

    hint_lbl = Gtk.Label(label="💡 Presiona Enter para buscar canciones • Esc para cerrar")
    hint_lbl.get_style_context().add_class("track-artist")
    hint_lbl.set_xalign(0)
    card.pack_start(hint_lbl, False, False, 0)

    # 3. Lista de resultados
    results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    liststore = Gtk.ListStore(str, str)
    treeview = Gtk.TreeView(model=liststore)
    treeview.set_headers_visible(False)
    treeview.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=0))

    def on_select(_tv, path, _col):
        it = liststore.get_iter(path)
        if it:
            url = liststore.get_value(it, 1)
            player.play(url)
            win.destroy()

    treeview.connect("row-activated", on_select)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(140)
    scrolled.add(treeview)
    results_box.pack_start(scrolled, True, True, 0)
    card.pack_start(results_box, True, True, 0)

    # 4. Chips de acceso rápido
    chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    chips = [
        ("⭐ Favoritas", lambda: player.play_favorites()),
        ("☕ Lo-Fi", lambda: player.play("lofi hip hop radio beats to relax study")),
        ("🎻 Clásica", lambda: player.play("classical music for concentration studying")),
        ("🎷 Jazz", lambda: player.play("relaxing jazz instrumental coffee shop")),
        ("🎧 Bass Boost", lambda: player.set_equalizer("bass")),
    ]
    for label, action in chips:
        b = Gtk.Button(label=label)
        b.get_style_context().add_class("chip-btn")
        b.connect("clicked", lambda _w, act=action: (act(), win.destroy()))
        chips_box.pack_start(b, False, False, 0)
    card.pack_start(chips_box, False, False, 0)

    def on_search(_entry):
        q = entry.get_text().strip()
        if not q:
            return
        hint_lbl.set_text(f"⏳ Buscando '{q}'...")
        results_box.show_all()
        liststore.clear()

        def fetch():
            items = []
            try:
                cmd = ["yt-dlp", "--no-warnings", "--flat-playlist", "--print", "%(title)s\t%(id)s", f"ytsearch6:{q} audio"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                out, _ = proc.communicate(timeout=7)
                for line in out.strip().splitlines():
                    if "\t" in line:
                        t, vid = line.split("\t", 1)
                        items.append((t.strip(), f"https://www.youtube.com/watch?v={vid.strip()}"))
            except Exception:
                pass

            def show_items():
                if items:
                    hint_lbl.set_text("✅ Selecciona con las flechas o ratón y presiona Enter:")
                    for t, u in items:
                        liststore.append([f"🎵  {t}", u])
                    treeview.grab_focus()
                    it = liststore.get_iter_first()
                    if it:
                        treeview.get_selection().select_iter(it)
                else:
                    hint_lbl.set_text("❌ No se encontraron resultados.")
            GLib.idle_add(show_items)

        threading.Thread(target=fetch, daemon=True).start()

    entry.connect("activate", on_search)

    win.connect("key-press-event", lambda _w, e: win.destroy() if e.keyval == Gdk.KEY_Escape else False)
    win.connect("focus-out-event", lambda _w, _e: win.destroy())
    win.connect("destroy", Gtk.main_quit)

    win.show_all()
    results_box.hide()
    entry.grab_focus()
    Gtk.main()


def show_spotlight_tkinter(initial_query=""):
    """Lanza la ventana flotante Spotlight / Raycast usando Tkinter (nativo en Windows y macOS)."""
    try:
        import tkinter as tk
    except ImportError:
        print("Interfaz gráfica no disponible. Usa la consola: python main.py play <canción>")
        return

    root = tk.Tk()
    root.title("Spotlight Music")
    root.configure(bg="#121217")
    root.attributes("-topmost", True)

    w, h = 520, 180
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.resizable(False, False)

    frame = tk.Frame(root, bg="#121217", padx=20, pady=16)
    frame.pack(fill=tk.BOTH, expand=True)

    title, paused, activo = player.get_status()
    header_text = f"🎵 {title[:40]}..." if (activo and title) else "🎵 Spotlight Music"
    if paused:
        header_text += " (Pausado)"

    lbl_status = tk.Label(frame, text=header_text, bg="#121217", fg="#ffffff", font=("Segoe UI", 11, "bold"), anchor="w")
    lbl_status.pack(fill=tk.X, pady=(0, 10))

    ctrl_frame = tk.Frame(frame, bg="#121217")
    ctrl_frame.pack(fill=tk.X, pady=(0, 12))

    def do_pause():
        player.pause()
        t, p, a = player.get_status()
        lbl_status.config(text=(f"🎵 {t[:40]}..." if t else "🎵 Spotlight Music") + (" (Pausado)" if p else ""))

    def do_next():
        player.next_track()

    def do_prev():
        player.prev_track()

    def do_lyrics():
        threading.Thread(target=lyrics.show_lyrics_window, daemon=True).start()

    def do_fav():
        ok, msg = player.save_favorite()
        lbl_status.config(text=f"⭐ {msg}")

    btn_style = {"bg": "#22232e", "fg": "#c5c8d6", "activebackground": "#303242", "activeforeground": "#ffffff", "bd": 0, "padx": 10, "pady": 4, "font": ("Segoe UI", 9, "bold"), "cursor": "hand2"}

    tk.Button(ctrl_frame, text="⏮ Prev", command=do_prev, **btn_style).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(ctrl_frame, text="⏯ Pausa", command=do_pause, **btn_style).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(ctrl_frame, text="⏭ Next", command=do_next, **btn_style).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(ctrl_frame, text="❤️ Fav", command=do_fav, **btn_style).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(ctrl_frame, text="🎤 Letra", command=do_lyrics, **btn_style).pack(side=tk.LEFT, padx=(0, 6))

    entry = tk.Entry(frame, bg="#1c1d26", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 12), bd=0, highlightthickness=1, highlightbackground="#353748", highlightcolor="#6366f1")
    entry.pack(fill=tk.X, pady=(0, 8), ipady=6)
    if initial_query:
        entry.insert(0, initial_query)
    entry.focus_set()

    lbl_info = tk.Label(frame, text="Escribe una canción o artista y presiona Enter • Esc para cerrar", bg="#121217", fg="#7a7f98", font=("Segoe UI", 9))
    lbl_info.pack(fill=tk.X)

    def on_enter(event=None):
        q = entry.get().strip()
        if q:
            lbl_info.config(text="🔍 Conectando con YouTube Music...", fg="#818cf8")
            lbl_status.config(text=f"⏳ Buscando: {q}...")
            root.update()

            def start_bg():
                ok = player.play(q)
                if not ok:
                    lbl_status.config(text="❌ Error al iniciar reproductor")
                    lbl_info.config(text="Verifica tu conexión o los componentes de audio", fg="#ef4444")
                    return
                for _ in range(25):
                    time.sleep(0.5)
                    t, p, a = player.get_status()
                    if a and t and player.es_titulo_valido(t):
                        lbl_status.config(text=f"🎵 {t[:38]}...")
                        lbl_info.config(text="▶️ Reproduciendo ahora • Esc para cerrar", fg="#34d399")
                        break

            threading.Thread(target=start_bg, daemon=True).start()

    def auto_refresh():
        try:
            t, p, a = player.get_status()
            if a and t and player.es_titulo_valido(t):
                text = f"🎵 {t[:38]}..."
                if p:
                    text += " (Pausado)"
                lbl_status.config(text=text)
            root.after(2000, auto_refresh)
        except Exception:
            pass

    entry.bind("<Return>", on_enter)
    root.bind("<Escape>", lambda e: root.destroy())
    root.after(2000, auto_refresh)

    root.mainloop()


def run_tray():
    """Ejecuta el icono en la barra de tareas."""
    if sys.platform.startswith("linux"):
        # En Linux usamos AyatanaAppIndicator para máxima integración con GNOME/KDE
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import Gtk, AyatanaAppIndicator3, GLib

            indicator = AyatanaAppIndicator3.Indicator.new(
                "spotlight-music-tray",
                "audio-headphones-symbolic",
                AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
            menu = Gtk.Menu()
            indicator.set_menu(menu)

            def update_menu():
                for c in menu.get_children():
                    menu.remove(c)
                title, paused, activo = player.get_status()
                if activo and title:
                    lbl = title[:30] + "..." if len(title) > 33 else title
                    i_np = Gtk.MenuItem(label=f"🎵 {lbl}")
                    i_np.connect("activate", lambda _: show_spotlight_player())
                    menu.append(i_np)

                    i_p = Gtk.MenuItem(label="▶️ Reanudar" if paused else "⏸️ Pausar")
                    i_p.connect("activate", lambda _: player.pause())
                    menu.append(i_p)

                    i_next = Gtk.MenuItem(label="⏭️ Siguiente canción")
                    i_next.connect("activate", lambda _: player.next_track())
                    menu.append(i_next)

                    i_l = Gtk.MenuItem(label="🎤 Ver letra...")
                    i_l.connect("activate", lambda _: lyrics.show_lyrics_window())
                    menu.append(i_l)

                    menu.append(Gtk.SeparatorMenuItem())
                    i_search = Gtk.MenuItem(label="🔍 Buscar (Spotlight)...")
                    i_search.connect("activate", lambda _: show_spotlight_player())
                    menu.append(i_search)

                    i_stop = Gtk.MenuItem(label="⏹️ Detener música")
                    i_stop.connect("activate", lambda _: player.stop())
                    menu.append(i_stop)
                else:
                    i_search = Gtk.MenuItem(label="🔍 Buscar música (Spotlight)...")
                    i_search.connect("activate", lambda _: show_spotlight_player())
                    menu.append(i_search)

                    i_favs = Gtk.MenuItem(label="⭐ Reproducir Favoritas")
                    i_favs.connect("activate", lambda _: player.play_favorites())
                    menu.append(i_favs)

                menu.show_all()
                return True

            update_menu()
            GLib.timeout_add_seconds(2, update_menu)
            Gtk.main()
            return
        except Exception:
            pass

    # Soporte para Windows / macOS mediante pystray
    try:
        import pystray
        from PIL import Image, ImageDraw

        def create_tray_image():
            img = Image.new('RGB', (64, 64), color=(18, 18, 23))
            d = ImageDraw.Draw(img)
            d.ellipse((10, 10, 54, 54), fill=(99, 102, 241))
            return img

        def on_open(icon, item):
            threading.Thread(target=show_spotlight_player, daemon=True).start()

        def on_pause(icon, item):
            player.pause()

        def on_next(icon, item):
            player.next_track()

        def on_lyrics(icon, item):
            threading.Thread(target=lyrics.show_lyrics_window, daemon=True).start()

        def on_exit(icon, item):
            icon.stop()

        tray_menu = pystray.Menu(
            pystray.MenuItem("🔍 Buscar música", on_open, default=True),
            pystray.MenuItem("⏯️ Pausar / Reanudar", on_pause),
            pystray.MenuItem("⏭️ Siguiente", on_next),
            pystray.MenuItem("🎤 Ver letra", on_lyrics),
            pystray.MenuItem("❌ Salir", on_exit)
        )
        icon = pystray.Icon("SpotlightMusic", create_tray_image(), "Spotlight Music", tray_menu)
        icon.run()
        return
    except Exception:
        pass

    # Si no hay bandeja gráfica disponible, abrir ventana Spotlight
    show_spotlight_player()


def print_help():
    print("""
🎵 Spotlight Music - Control de Música
======================================
Uso:
  python main.py                     -> Inicia el mini-reproductor / bandeja
  python main.py search [canción]    -> Abre la ventana flotante de búsqueda
  python main.py play <canción>      -> Reproduce un tema directamente
  python main.py pause               -> Pausa o reanuda la música
  python main.py next                -> Pasa a la siguiente canción
  python main.py prev                -> Vuelve a la canción anterior
  python main.py stop                -> Detiene la música
  python main.py lyrics              -> Muestra la letra de la canción actual
  python main.py bass/voz/plano      -> Aplica ecualización en tiempo real
    """)


def main():
    args = sys.argv[1:]
    if not args:
        show_spotlight_player()
    elif args[0] in ("tray", "--tray"):
        run_tray()
    elif args[0] in ("search", "gui", "-s"):
        q = " ".join(args[1:]) if len(args) > 1 else ""
        show_spotlight_player(q)
    elif args[0] == "play":
        player.play(" ".join(args[1:]))
    elif args[0] in ("pause", "pausa"):
        player.pause()
    elif args[0] in ("next", "siguiente"):
        player.next_track()
    elif args[0] in ("prev", "anterior"):
        player.prev_track()
    elif args[0] in ("stop", "parar"):
        player.stop()
    elif args[0] in ("lyrics", "letra"):
        lyrics.show_lyrics_window()
    elif args[0] in ("bass", "voz", "brillo", "plano"):
        player.set_equalizer(args[0])
    elif args[0] in ("favs", "favoritas"):
        player.play_favorites()
    elif args[0] in ("like", "fav"):
        ok, msg = player.save_favorite()
        print(msg)
    elif args[0] in ("help", "--help", "-h"):
        print_help()
    else:
        # Por defecto reproducir lo que se escriba
        player.play(" ".join(args))


if __name__ == "__main__":
    main()
