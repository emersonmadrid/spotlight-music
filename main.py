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

import player
import lyrics


def show_spotlight_player(initial_query=""):
    """Lanza la ventana flotante Spotlight / Raycast."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk, GLib
    except ImportError:
        print("GTK3 no está disponible en este entorno. Usa la interfaz de consola: python main.py play <canción>")
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
        except Exception as e:
            print("No se pudo iniciar el AppIndicator en Linux, pasando a consola:", e)

    # Si estamos en Windows o no hay GTK disponible
    print("Iniciando reproductor de música en segundo plano...")
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


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
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
    else:
        # Por defecto reproducir lo que se escriba
        player.play(" ".join(args))
