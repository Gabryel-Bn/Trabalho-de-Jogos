"""Célula individual do terreno e sua sprite procedural."""

import pygame

from config import (
    GRASS, GRASS_ALT, GRASS_DARK, GRID_X, GRID_Y, ROCK, ROCK_ALT,
    ROCK_DARK, TILE_SIZE,
)


class Tile:
    """Uma célula do mapa, com aparência e propriedade de colisão próprias."""

    _sprites: dict[tuple[bool, int, int], pygame.Surface] = {}

    def __init__(self, col: int, row: int, solid: bool = False) -> None:
        self.col = col
        self.row = row
        self.solid = solid

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(GRID_X + self.col * TILE_SIZE, GRID_Y + self.row * TILE_SIZE,
                           TILE_SIZE, TILE_SIZE)

    def _sprite(self) -> pygame.Surface:
        key = (self.solid, self.col, self.row)
        if key not in self._sprites:
            variant = (self.col * 17 + self.row * 31 + self.col * self.row * 7) % 5
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            if self.solid:
                base = ROCK_ALT if variant in (1, 4) else ROCK
                pygame.draw.rect(surface, base, (0, 0, TILE_SIZE, TILE_SIZE))
                pygame.draw.line(surface, (145, 151, 149), (7, 12 + variant), (20, 9 + variant), 2)
                pygame.draw.line(surface, ROCK_DARK, (29, 34 - variant), (40, 31 - variant), 2)
                pygame.draw.circle(surface, (91, 100, 101), (9 + (self.col * 11) % 30, 34), 2)
            else:
                base = GRASS_ALT if variant in (0, 3) else GRASS
                pygame.draw.rect(surface, base, (0, 0, TILE_SIZE, TILE_SIZE))
                gx = 9 + (self.col * 13 + self.row * 5) % 28
                gy = 10 + (self.row * 17 + self.col * 3) % 28
                pygame.draw.line(surface, GRASS_DARK, (gx, gy + 5), (gx - 2, gy), 2)
                pygame.draw.line(surface, (182, 190, 117), (gx, gy + 5), (gx + 3, gy + 1), 2)
                pygame.draw.circle(surface, (113, 163, 99), (38 - gx // 3, 12 + gy // 2), 1)
            self._sprites[key] = surface
        return self._sprites[key]

    def draw(self, target: pygame.Surface) -> None:
        target.blit(self._sprite(), self.rect.topleft)
