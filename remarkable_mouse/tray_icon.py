from PIL import Image, ImageDraw
import pystray
import threading
import os
import sys

def create_tray_icon(on_quit=None, screens=None, on_screen_select=None):
    # Le menu "Gestures" contrôle touch_enabled (et donc les gestures)
    if not hasattr(create_tray_icon, 'touch_enabled'):
        create_tray_icon.touch_enabled = False
        # Synchronise la variable globale du module pen au démarrage
        try:
            import remarkable_mouse.pen as pen_mod
            pen_mod.gestures_enabled = False
        except Exception:
            pass

    def toggle_gestures(icon, item):
        create_tray_icon.touch_enabled = not create_tray_icon.touch_enabled
        # Synchronise la variable globale du module pen si possible
        try:
            import remarkable_mouse.pen as pen_mod
            pen_mod.gestures_enabled = create_tray_icon.touch_enabled
        except Exception:
            pass
        icon.update_menu()

    def checked_gestures(item):
        return create_tray_icon.touch_enabled
    # Génère une icône carrée rouge bien visible
    image = Image.new('RGB', (64, 64), color=(255, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((8, 8, 56, 56), fill=(255, 255, 255))

    import os
    def quit_action(icon, item):
        icon.stop()
        os._exit(0)  # Forcer la terminaison immédiate de tout le process

    # Ajout d'un indicateur visuel pour l'écran sélectionné
    # On stocke l'index sélectionné dans l'icône (attribut custom)
    if not hasattr(create_tray_icon, 'selected_screen'):
        create_tray_icon.selected_screen = 0

    def make_screen_action(idx):
        def _action(icon, item):
            create_tray_icon.selected_screen = idx
            if on_screen_select:
                on_screen_select(idx)
        return _action

    # Ajout d'un bouton pour activer/désactiver le touch
    if not hasattr(create_tray_icon, 'touch_enabled'):
        create_tray_icon.touch_enabled = True

    def toggle_touch(icon, item):
        create_tray_icon.touch_enabled = not create_tray_icon.touch_enabled
        icon.update_menu()

    def checked_touch(item):
        return create_tray_icon.touch_enabled

    def build_menu():
        screen_items = []
        if screens:
            for i, screen in enumerate(screens):
                label = f"Écran {i+1} ({screen.width}x{screen.height})"
                def checked(item, idx=i):
                    return create_tray_icon.selected_screen == idx
                screen_items.append(pystray.MenuItem(
                    label,
                    make_screen_action(i),
                    checked=checked
                ))
        return pystray.Menu(
            *(screen_items + [
                pystray.MenuItem('Gestures', toggle_gestures, checked=checked_gestures, default=False),
                pystray.MenuItem('Quitter', quit_action)
            ])
        )

    icon = pystray.Icon('remarkable_mouse', image, 'reMarkable Mouse', build_menu())
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
