"""Mapa de tiles, regras de colisão e posicionamento automático das bordas."""

import random

import pygame

from config import COLS, EDGE, EDGE_HI, GRID_H, GRID_W, GRID_X, GRID_Y, ROWS, TILE_SIZE
from tile import Tile


class TileMap:
    """Gerencia as células, a pintura e as bordas automáticas do mapa."""

    def __init__(self, cols: int = COLS, rows: int = ROWS) -> None:
        self.cols = cols
        self.rows = rows
        self.tiles = [[Tile(x, y) for x in range(cols)] for y in range(rows)]
        self.load_example()

    def load_example(self) -> None:
        for x, y, width, height in ((2, 2, 3, 2), (8, 1, 3, 3), (5, 6, 4, 2), (10, 7, 2, 2)):
            for row in range(y, min(y + height, self.rows)):
                for col in range(x, min(x + width, self.cols)):
                    self.tiles[row][col].solid = True
        for x, y in ((3, 1), (4, 1), (7, 3), (8, 4), (4, 7), (9, 7), (9, 8), (1, 6)):
            self.tiles[y][x].solid = True

    def tile_at_pixel(self, pos: tuple[int, int]) -> Tile | None:
        col = (pos[0] - GRID_X) // TILE_SIZE
        row = (pos[1] - GRID_Y) // TILE_SIZE
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.tiles[row][col]
        return None

    def paint(self, pos: tuple[int, int], solid: bool) -> None:
        tile = self.tile_at_pixel(pos)
        if tile is not None:
            tile.solid = solid

    def clear(self) -> None:
        for row in self.tiles:
            for tile in row:
                tile.solid = False

    def randomize(self) -> None:
        for row in self.tiles:
            for tile in row:
                tile.solid = random.random() < 0.28

    def is_blocked(self, rect: pygame.Rect) -> bool:
        if (rect.left < GRID_X or rect.top < GRID_Y
                or rect.right > GRID_X + GRID_W or rect.bottom > GRID_Y + GRID_H):
            return True
        left = (rect.left - GRID_X) // TILE_SIZE
        right = (rect.right - 1 - GRID_X) // TILE_SIZE
        top = (rect.top - GRID_Y) // TILE_SIZE
        bottom = (rect.bottom - 1 - GRID_Y) // TILE_SIZE
        return any(self.tiles[y][x].solid
                   for y in range(top, bottom + 1)
                   for x in range(left, right + 1))

    def _draw_borders(self, target: pygame.Surface) -> None:
        # Cada lado compara o estado da célula com o do vizinho; a borda é
        # independente das sprites dos dois terrenos (método desacoplado).
        directions = ((0, -1), (1, 0), (0, 1), (-1, 0))
        for row in range(self.rows):
            for col in range(self.cols):
                tile = self.tiles[row][col]
                x, y = tile.rect.topleft
                endpoints = (
                    ((x, y), (x + TILE_SIZE, y)),
                    ((x + TILE_SIZE, y), (x + TILE_SIZE, y + TILE_SIZE)),
                    ((x, y + TILE_SIZE), (x + TILE_SIZE, y + TILE_SIZE)),
                    ((x, y), (x, y + TILE_SIZE)),
                )
                for (dx, dy), (start, end) in zip(directions, endpoints):
                    nx, ny = col + dx, row + dy
                    neighbor_solid = (
                        self.tiles[ny][nx].solid
                        if 0 <= nx < self.cols and 0 <= ny < self.rows
                        else False
                    )
                    if neighbor_solid != tile.solid:
                        pygame.draw.line(target, EDGE, start, end, 4)
                        highlight = EDGE_HI if tile.solid else (137, 184, 113)
                        pygame.draw.line(target, highlight,
                                         (start[0], start[1] + 1),
                                         (end[0], end[1] + 1), 1)

    def draw(self, target: pygame.Surface) -> None:
        for row in self.tiles:
            for tile in row:
                tile.draw(target)
        self._draw_borders(target)
        for col in range(self.cols + 1):
            x = GRID_X + col * TILE_SIZE
            pygame.draw.line(target, (64, 83, 72), (x, GRID_Y), (x, GRID_Y + GRID_H), 1)
        for row in range(self.rows + 1):
            y = GRID_Y + row * TILE_SIZE
            pygame.draw.line(target, (64, 83, 72), (GRID_X, y), (GRID_X + GRID_W, y), 1)

    @property
    def solid_count(self) -> int:
        return sum(tile.solid for row in self.tiles for tile in row)
