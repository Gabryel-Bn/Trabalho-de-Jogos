"""Personagem da demonstração e sua colisão com o mapa."""

import pygame

from config import GRID_X, GRID_Y, PLAYER_COLOR, PLAYER_DARK, TILE_SIZE
from tile_map import TileMap


class Player:
    """Personagem que se move pelo chão livre e colide com as pedras."""

    def __init__(self, tile_map: TileMap) -> None:
        self.rect = pygame.Rect(GRID_X + TILE_SIZE // 2 - 11,
                                GRID_Y + TILE_SIZE // 2 - 11, 22, 22)
        self.speed = 190
        self.tile_map = tile_map

    def move(self, dx: float, dy: float) -> None:
        self.rect.x += round(dx)
        if self.tile_map.is_blocked(self.rect):
            self.rect.x -= round(dx)
        self.rect.y += round(dy)
        if self.tile_map.is_blocked(self.rect):
            self.rect.y -= round(dy)

    def draw(self, target: pygame.Surface) -> None:
        pygame.draw.rect(target, PLAYER_DARK, self.rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(target, PLAYER_COLOR, self.rect, border_radius=7)
        pygame.draw.circle(target, (57, 53, 40), (self.rect.centerx - 4, self.rect.centery - 2), 2)
        pygame.draw.circle(target, (57, 53, 40), (self.rect.centerx + 4, self.rect.centery - 2), 2)
