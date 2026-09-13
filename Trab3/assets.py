"""Carregamento dos sprites CC0 usados pelo jogo."""
from pathlib import Path
import pygame

ASSET_DIR = Path(__file__).parent / "assets"


def _load(path):
    image = pygame.image.load(ASSET_DIR / path).convert_alpha()
    return image


def load_soldier():
    """Usa o primeiro soldado da segunda linha da folha 4x4."""
    sheet = _load("soldiers_cc0.png")
    tile_size = sheet.get_width() // 4
    sprite = sheet.subsurface(pygame.Rect(0, tile_size, tile_size, tile_size)).copy()
    sprite.set_colorkey(sprite.get_at((0, 0)))
    return pygame.transform.smoothscale(sprite, (48, 48))


def load_zombie():
    sprite = _load("zombie_cc0.png")
    sprite.set_colorkey(sprite.get_at((0, 0)))
    return pygame.transform.smoothscale(sprite, (42, 42))


def load_ship():
    sprite = _load("ship_cc0.png")
    sprite.set_colorkey(sprite.get_at((0, 0)))
    return pygame.transform.smoothscale(sprite, (64, 64))
