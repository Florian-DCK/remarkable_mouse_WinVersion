from PIL import Image, ImageDraw
import pystray
import threading
import os
import sys

def create_tray_icon(on_quit=None):
    # Génère une icône carrée rouge bien visible
    image = Image.new('RGB', (64, 64), color=(255, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((8, 8, 56, 56), fill=(255, 255, 255))

    import os
    def quit_action(icon, item):
        icon.stop()
        os._exit(0)  # Forcer la terminaison immédiate de tout le process

    menu = pystray.Menu(
        pystray.MenuItem('Quitter', quit_action)
    )
    icon = pystray.Icon('remarkable_mouse', image, 'reMarkable Mouse', menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
