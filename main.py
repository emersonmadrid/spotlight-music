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
import single_instance

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
except ImportError:
    tk = None


def show_spotlight_player(initial_query="", start_hidden=False):
    """Lanza la ventana flotante Spotlight / Raycast."""
    if sys.platform.startswith("win"):
        show_spotlight_tkinter(initial_query, start_hidden=start_hidden)
        return

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk, GLib
    except (ImportError, ValueError):
        # Fallback universal nativo (Windows, macOS o Linux sin GTK3)
        show_spotlight_tkinter(initial_query, start_hidden=start_hidden)
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
                ytdlp_bin = player.get_ytdlp_path() if hasattr(player, 'get_ytdlp_path') else "yt-dlp"
                cmd = [ytdlp_bin, "--no-warnings", "--flat-playlist", "--extractor-args", "youtube:player_client=android,web_creator", "--print", "%(title)s\t%(id)s", f"ytsearch6:{q} audio"]
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


def show_spotlight_tkinter(initial_query="", start_hidden=False):
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

    app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    icon_ico = os.path.join(app_dir, "spotlight.ico")
    if os.path.exists(icon_ico):
        try:
            root.iconbitmap(icon_ico)
        except Exception:
            pass

    w = 540
    h_base = 220
    h_expanded = 430
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = max(50, (sh - h_expanded) // 2)
    root.geometry(f"{w}x{h_base}+{x}+{y}")
    root.resizable(False, False)

    def show_window():
        root.deiconify()
        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.attributes("-topmost", False)
        entry.focus_set()

    def hide_to_tray(event=None):
        root.withdraw()

    tray_icon_holder = [None]

    def quit_app():
        player.stop()
        if tray_icon_holder[0]:
            try:
                tray_icon_holder[0].stop()
            except Exception:
                pass
        try:
            root.destroy()
        except Exception:
            pass
        sys.exit(0)

    # Registro de instancia única: si ya corre otra instancia, la nueva notifica y se cierra
    def on_single_instance_command(data):
        def process():
            if data:
                parts = data.split(" ", 1)
                sub_arg = parts[1].strip() if len(parts) > 1 else ""
                if sub_arg and sub_arg != "--tray":
                    if sub_arg.startswith("play "):
                        player.play(sub_arg[5:].strip())
                    else:
                        entry.delete(0, tk.END)
                        entry.insert(0, sub_arg)
                        on_search()
            show_window()
        root.after(0, process)

    single_instance.check_and_bind_single_instance(on_single_instance_command)

    # Inicialización de la bandeja del sistema (System Tray)
    def init_tray():
        try:
            import pystray
            from PIL import Image

            icon_png = os.path.join(app_dir, "spotlight.png")
            if os.path.exists(icon_png):
                img = Image.open(icon_png)
            else:
                img = Image.new('RGB', (64, 64), color=(99, 102, 241))

            def on_tray_open(icon, item):
                root.after(0, show_window)

            def on_tray_pause(icon, item):
                player.pause()

            def on_tray_next(icon, item):
                player.next_track()

            def on_tray_prev(icon, item):
                player.prev_track()

            def on_tray_fav(icon, item):
                player.save_favorite()

            def on_tray_exit(icon, item):
                root.after(0, quit_app)

            menu = pystray.Menu(
                pystray.MenuItem("🔍 Abrir Spotlight Music", on_tray_open, default=True),
                pystray.MenuItem("⏯️ Pausar / Reanudar", on_tray_pause),
                pystray.MenuItem("⏭️ Siguiente canción", on_tray_next),
                pystray.MenuItem("⏮️ Canción anterior", on_tray_prev),
                pystray.MenuItem("⭐ Guardar en Favoritas", on_tray_fav),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Salir de Spotlight Music", on_tray_exit)
            )
            tray_icon_holder[0] = pystray.Icon("SpotlightMusic", img, "Spotlight Music", menu)
            tray_icon_holder[0].run()
        except Exception:
            pass

    threading.Thread(target=init_tray, daemon=True).start()

    main_card = tk.Frame(root, bg="#121217", padx=18, pady=16)
    main_card.pack(fill=tk.BOTH, expand=True)

    # 1. Tarjeta Superior Now Playing
    np_card = tk.Frame(main_card, bg="#181922", highlightthickness=1, highlightbackground="#282937", padx=14, pady=10)
    np_card.pack(fill=tk.X, pady=(0, 12))

    info_box = tk.Frame(np_card, bg="#181922")
    info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    title, paused, activo = player.get_status()
    lbl_title = tk.Label(
        info_box,
        text=f"🎵 {title[:32]}..." if (activo and title) else "🎵 Spotlight Music",
        bg="#181922", fg="#ffffff", font=("Segoe UI", 11, "bold"), anchor="w"
    )
    lbl_title.pack(fill=tk.X)

    cur, dur = player.get_playback_time()
    time_str = f" [{cur} / {dur}]" if cur else ""
    sub_text = ("▶ Reproduciendo ahora" + time_str) if activo else "Listo para reproducir música"
    if paused:
        sub_text = "⏸ En pausa" + time_str
    lbl_sub = tk.Label(info_box, text=sub_text, bg="#181922", fg="#8c92a6", font=("Segoe UI", 9), anchor="w")
    lbl_sub.pack(fill=tk.X, pady=(2, 0))

    ctrl_box = tk.Frame(np_card, bg="#181922")
    ctrl_box.pack(side=tk.RIGHT, padx=(8, 0))

    def make_btn(parent, text, cmd):
        b = tk.Button(
            parent, text=text, command=cmd, bg="#252633", fg="#ffffff",
            activebackground="#353648", activeforeground="#ffffff", bd=0, padx=8, pady=4,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        b.bind("<Enter>", lambda e: b.config(bg="#353648"))
        b.bind("<Leave>", lambda e: b.config(bg="#252633"))
        return b

    def do_pause():
        player.pause()
        t, p, a = player.get_status()
        btn_pause.config(text="▶" if p else "⏸")
        lbl_sub.config(text="⏸ En pausa" if p else "▶ Reproduciendo ahora")

    def do_next():
        player.next_track()
        lbl_title.config(text="⏳ Cargando canción...")
        lbl_sub.config(text="Saltando pista...")

    def do_prev():
        player.prev_track()
        lbl_title.config(text="⏳ Cargando canción...")
        lbl_sub.config(text="Volviendo a anterior...")

    def do_fav():
        ok, msg = player.save_favorite()
        btn_fav.config(text="💖")
        root.after(1500, lambda: btn_fav.config(text="❤️"))
        lbl_sub.config(text=f"⭐ {msg}")

    btn_prev = make_btn(ctrl_box, "⏮", do_prev)
    btn_prev.pack(side=tk.LEFT, padx=2)
    btn_pause = make_btn(ctrl_box, "▶" if paused else "⏸", do_pause)
    btn_pause.pack(side=tk.LEFT, padx=2)
    btn_next = make_btn(ctrl_box, "⏭", do_next)
    btn_next.pack(side=tk.LEFT, padx=2)
    btn_fav = make_btn(ctrl_box, "❤️", do_fav)
    btn_fav.pack(side=tk.LEFT, padx=2)
    btn_lyr = make_btn(ctrl_box, "🎤", lambda: threading.Thread(target=lyrics.show_lyrics_window, daemon=True).start())
    btn_lyr.pack(side=tk.LEFT, padx=2)
    btn_hide = make_btn(ctrl_box, "✕", hide_to_tray)
    btn_hide.pack(side=tk.LEFT, padx=(5, 0))

    # 2. Entrada de búsqueda
    entry_frame = tk.Frame(main_card, bg="#181922", highlightthickness=1, highlightbackground="#353748", padx=12, pady=8)
    entry_frame.pack(fill=tk.X, pady=(0, 6))

    placeholder_text = "🔍 Escribe cualquier canción, artista o género..."
    entry = tk.Entry(
        entry_frame, bg="#181922", fg="#7a7f98", insertbackground="#ffffff",
        font=("Segoe UI", 11), bd=0
    )
    if initial_query:
        entry.insert(0, initial_query)
        entry.config(fg="#ffffff")
    else:
        entry.insert(0, placeholder_text)
    entry.pack(fill=tk.X)

    def on_focus_in(event):
        entry_frame.config(highlightbackground="#6366f1")
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(fg="#ffffff")

    def on_focus_out(event):
        entry_frame.config(highlightbackground="#353748")
        if not entry.get().strip():
            entry.insert(0, placeholder_text)
            entry.config(fg="#7a7f98")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

    lbl_hint = tk.Label(
        main_card, text="💡 Presiona Enter para buscar • Esc o ✕ para minimizar a la bandeja",
        bg="#121217", fg="#7a7f98", font=("Segoe UI", 8), anchor="w"
    )
    lbl_hint.pack(fill=tk.X, pady=(0, 8))

    # 3. Lista de resultados (inicialmente oculta)
    results_frame = tk.Frame(main_card, bg="#171822", highlightthickness=1, highlightbackground="#282937", padx=4, pady=4)
    result_items = []

    listbox = tk.Listbox(
        results_frame, bg="#171822", fg="#e2e4ee", selectbackground="#2e3040",
        selectforeground="#ffffff", font=("Segoe UI", 10), bd=0, highlightthickness=0,
        activestyle="none", height=6
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    def on_select_result(event=None):
        sel = listbox.curselection()
        if sel and sel[0] < len(result_items):
            title, url = result_items[sel[0]]
            lbl_title.config(text=f"⏳ Cargando: {title[:32]}...")
            lbl_sub.config(text="Iniciando streaming...")
            root.update()
            player.play(url)

    listbox.bind("<Double-Button-1>", on_select_result)
    listbox.bind("<Return>", on_select_result)

    # 4. Chips de acceso rápido
    chips_frame = tk.Frame(main_card, bg="#121217")
    chips_frame.pack(fill=tk.X)

    def make_chip(parent, text, action):
        def on_click():
            lbl_title.config(text=f"⏳ Activando: {text}...")
            lbl_sub.config(text="Cargando playlist / perfil...")
            root.update()
            action()

        b = tk.Button(
            parent, text=text, command=on_click,
            bg="#1a1a24", fg="#b0b4c8", activebackground="#272836", activeforeground="#ffffff",
            bd=0, padx=9, pady=5, font=("Segoe UI", 9), cursor="hand2"
        )
        b.bind("<Enter>", lambda e: b.config(bg="#272836", fg="#ffffff"))
        b.bind("<Leave>", lambda e: b.config(bg="#1a1a24", fg="#b0b4c8"))
        return b

    chips = [
        ("⭐ Favoritas", lambda: player.play_favorites()),
        ("☕ Lo-Fi", lambda: player.play("lofi hip hop radio beats to relax study")),
        ("🎻 Clásica", lambda: player.play("classical music for concentration studying")),
        ("🎷 Jazz", lambda: player.play("relaxing jazz instrumental coffee shop")),
        ("🎧 Bass Boost", lambda: player.set_equalizer("bass")),
    ]
    for label, act in chips:
        make_chip(chips_frame, label, act).pack(side=tk.LEFT, padx=(0, 6))

    def on_search(event=None):
        q = entry.get().strip()
        if not q or q == placeholder_text:
            return

        lbl_hint.config(text=f"⏳ Buscando '{q}' en YouTube...")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12), before=chips_frame)
        root.geometry(f"{w}x{h_expanded}+{x}+{y}")
        listbox.delete(0, tk.END)
        result_items.clear()
        listbox.insert(tk.END, "  ⏳ Cargando resultados...")
        root.update()

        def fetch():
            items = []
            # 1. Búsqueda directa en memoria usando yt_dlp (máxima velocidad, sin procesos externos)
            try:
                import yt_dlp
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web_creator']}},
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    res = ydl.extract_info(f"ytsearch6:{q} audio", download=False)
                    for entry_data in res.get('entries', []):
                        t = entry_data.get('title')
                        vid = entry_data.get('id')
                        if t and vid:
                            items.append((t.strip(), f"https://www.youtube.com/watch?v={vid.strip()}"))
            except Exception:
                pass

            # 2. Respaldo por si el módulo interno no resuelve
            if not items:
                try:
                    ytdlp_bin = player.get_ytdlp_path() if hasattr(player, 'get_ytdlp_path') else "yt-dlp"
                    cmd = [ytdlp_bin, "--no-warnings", "--flat-playlist", "--extractor-args", "youtube:player_client=android,web_creator", "--print", "%(title)s\t%(id)s", f"ytsearch6:{q} audio"]
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    out, _ = proc.communicate(timeout=8)
                    for line in out.strip().splitlines():
                        if "\t" in line:
                            t, vid = line.split("\t", 1)
                            items.append((t.strip(), f"https://www.youtube.com/watch?v={vid.strip()}"))
                except Exception:
                    pass

            def update_ui():
                listbox.delete(0, tk.END)
                result_items.clear()
                if items:
                    lbl_hint.config(text="✅ Usa ↑ / ↓ y presiona Enter para reproducir:")
                    for t, u in items:
                        result_items.append((t, u))
                        listbox.insert(tk.END, f"  🎵  {t}")
                    listbox.selection_set(0)
                    listbox.focus_set()
                else:
                    lbl_hint.config(text="❌ No se encontraron resultados. Presiona Enter para reproducir directo:")
                    result_items.append((q, q))
                    listbox.insert(tk.END, f"  ▶  Reproducir directo: '{q}'")
                    listbox.selection_set(0)
                    listbox.focus_set()
            root.after(0, update_ui)

        threading.Thread(target=fetch, daemon=True).start()

    entry.bind("<Return>", on_search)

    def on_down_arrow(event):
        if results_frame.winfo_ismapped() and listbox.size() > 0:
            listbox.focus_set()
            if not listbox.curselection():
                listbox.selection_set(0)

    entry.bind("<Down>", on_down_arrow)
    root.protocol("WM_DELETE_WINDOW", hide_to_tray)
    root.bind("<Escape>", hide_to_tray)

    def auto_refresh():
        try:
            t, p, a = player.get_status()
            if a and t and player.es_titulo_valido(t):
                cur, dur = player.get_playback_time()
                time_str = f" [{cur} / {dur}]" if cur else ""
                lbl_title.config(text=f"🎵 {t[:32]}...")
                lbl_sub.config(text=("⏸ En pausa" if p else "▶ Reproduciendo ahora") + time_str)
                btn_pause.config(text="▶" if p else "⏸")
                if tray_icon_holder[0]:
                    try:
                        tray_icon_holder[0].title = f"Spotlight Music: {t[:40]}"
                    except Exception:
                        pass
            root.after(1000, auto_refresh)
        except Exception:
            pass

    root.after(1000, auto_refresh)
    if start_hidden:
        root.withdraw()
    else:
        entry.focus_set()

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
        if sys.platform.startswith("win"):
            show_spotlight_player(start_hidden=True)
        else:
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
