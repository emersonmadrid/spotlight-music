"""
Módulo de Instancia Única para Spotlight Music.
Garantiza que sólo una instancia de la aplicación se ejecute simultáneamente.
Si el usuario intenta abrir otra instancia (ej. desde el acceso directo),
la segunda instancia le ordena a la primera que se muestre y finaliza inmediatamente.
"""

import os
import sys
import socket
import threading

PORT = 49281  # Puerto de señalización interna local

_server_socket = None
_lock_held = False


def check_and_bind_single_instance(on_command_callback=None):
    """
    Intenta adquirir el bloqueo de instancia única.
    Retorna True si es la primera instancia.
    Si ya existe otra instancia, le envía los argumentos de la línea de comandos y llama a sys.exit(0).
    """
    global _server_socket, _lock_held

    # En Windows, usar Named Mutex adicional como capa de protección nativa
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, False, "Local\\SpotlightMusic_SingleInstance_Mutex")
            if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                # Ya existe una instancia corriendo
                _notify_existing_instance()
                sys.exit(0)
        except Exception:
            pass

    # Bloqueo mediante Socket Localhost (100% confiable y multiplataforma)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', PORT))
        sock.listen(5)
        _server_socket = sock
        _lock_held = True

        def listen_loop():
            while True:
                try:
                    conn, _ = sock.accept()
                    data = conn.recv(1024).decode('utf-8', errors='ignore').strip()
                    conn.close()
                    if on_command_callback:
                        on_command_callback(data)
                except Exception:
                    break

        t = threading.Thread(target=listen_loop, daemon=True)
        t.start()
        return True
    except OSError:
        # Puerto ocupado -> Instancia ya existente
        _notify_existing_instance()
        sys.exit(0)


def _notify_existing_instance():
    """Conecta con la instancia activa y le pide mostrar la ventana o procesar argumentos."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2.0)
        client.connect(('127.0.0.1', PORT))
        cmd = "SHOW " + " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "SHOW"
        client.sendall(cmd.encode('utf-8'))
        client.close()
    except Exception:
        pass
