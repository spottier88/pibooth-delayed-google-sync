import os
import json
import socket
from pathlib import Path
import pygame
import pibooth
from pibooth.utils import LOGGER

SYNC_FILE = Path(__file__).parent / "sync_status.json"
SECTION = 'SYNCHRO'

def is_internet_available(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def load_synced():
    if SYNC_FILE.exists():
        return set(json.load(SYNC_FILE.open()))
    return set()

def save_synced(synced):
    SYNC_FILE.write_text(json.dumps(list(synced)))

@pibooth.hookimpl
def pibooth_configure(cfg):
    cfg.add_option(SECTION, 'enabled', True,
                   "Activer la synchronisation différée vers Google Photos",
                   "Activation synchronisation différée", ['False', 'True'])

@pibooth.hookimpl
def pibooth_startup(cfg, app):
    app.delayed_sync_enabled = cfg.getboolean(SECTION, 'enabled')
    app._delayed_sync_pending = False
    app._delayed_sync_done = False

@pibooth.hookimpl
def state_processing_exit(app, cfg):
    if not app.delayed_sync_enabled:
        return

    file_path = getattr(app, 'previous_picture_file', None)
    if not file_path or not os.path.exists(file_path):
        return

    if not is_internet_available():
        LOGGER.warning(f"[DelayedSync] Internet indisponible, ajout à la file : {file_path}")
        synced = load_synced()
        synced.add(str(file_path))
        save_synced(synced)

@pibooth.hookimpl
def state_wait_enter(cfg, app, win):
    if not app.delayed_sync_enabled:
        return

    synced = load_synced()
    if synced and is_internet_available() and hasattr(app, 'google_photos'):
        app._delayed_sync_pending = True
        app._delayed_sync_done = False

        win.surface.fill((0, 0, 0))
        font = pygame.font.SysFont("Arial", 30, bold=True)
        label = font.render("Synchronisation en cours...", True, (255, 255, 255))
        rect = label.get_rect(center=(win.surface.get_width() // 2, win.surface.get_height() // 2))
        win.surface.blit(label, rect)
        pygame.display.flip()

@pibooth.hookimpl
def state_wait_do(cfg, app, win, events):
    if app._delayed_sync_pending and not app._delayed_sync_done:
        synced = load_synced()
        album_name = cfg.get('GOOGLE', 'album_name', fallback="Pibooth")
        successful = set()

        for photo_path in synced:
            if not os.path.exists(photo_path):
                successful.add(photo_path)
                continue
            try:
                photo_id = app.google_photos.upload(photo_path, album_name)
                if photo_id:
                    LOGGER.info(f"[DelayedSync] Photo synchronisée : {photo_path}")
                    successful.add(photo_path)
                else:
                    LOGGER.warning(f"[DelayedSync] Échec : {photo_path}")
            except Exception as e:
                LOGGER.warning(f"[DelayedSync] Erreur : {e}")
                break

        remaining = set(synced) - successful
        save_synced(remaining)
        app._delayed_sync_done = True
        app._delayed_sync_pending = False
