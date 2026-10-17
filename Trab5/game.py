"""Ciclo principal e coordenação dos objetos do jogo."""

import pygame

from config import INK, SCREEN_H, SCREEN_W
from hud import HUD
from player import Player
from tile_map import TileMap


class Game:
    """Inicializa os objetos e controla o ciclo principal da demonstração."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Tiles automáticos — bordas desacopladas")
        self.clock = pygame.time.Clock()
        self.tile_map = TileMap()
        self.player = Player(self.tile_map)
        self.hud = HUD()
        self.running = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
            elif event.key == pygame.K_1:
                self.hud.brush_solid = True
            elif event.key == pygame.K_2:
                self.hud.brush_solid = False
            elif event.key == pygame.K_m:
                self.hud.brush_solid = not self.hud.brush_solid
            elif event.key == pygame.K_c:
                self.tile_map.clear()
                self.hud.notify("Mapa limpo")
            elif event.key == pygame.K_r:
                self.tile_map.randomize()
                self.hud.notify("Novo mapa gerado")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.hud.handle_click(event.pos):
                self.tile_map.paint(event.pos, self.hud.brush_solid)
            elif event.button == 3:
                self.tile_map.paint(event.pos, False)

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        horizontal = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        vertical = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        self.player.move(horizontal * self.player.speed * dt, vertical * self.player.speed * dt)
        self.hud.update(dt)

    def draw(self) -> None:
        self.screen.fill(INK)
        self.tile_map.draw(self.screen)
        self.player.draw(self.screen)
        self.hud.draw(self.screen, self.tile_map)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(60) / 1000, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()
