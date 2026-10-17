"""Interface visual, seleção do pincel e mensagens da demonstração."""

import pygame

from config import (
    ACCENT, GRID_H, GRID_W, GRID_X, GRID_Y, MUTED, PANEL, PANEL_LIGHT,
    PANEL_X, SCREEN_W, TEXT,
)
from tile_map import TileMap


class HUD:
    """Desenha cabeçalho, painel, botões e mensagens da interface."""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont("segoeui", 18)
        self.small_font = pygame.font.SysFont("segoeui", 14)
        self.title_font = pygame.font.SysFont("segoeui", 27, bold=True)
        self.brush_solid = True
        self.message = ""
        self.message_time = 0.0
        self.solid_button = pygame.Rect(PANEL_X + 18, GRID_Y + 88, 272, 40)
        self.free_button = pygame.Rect(PANEL_X + 18, GRID_Y + 136, 272, 40)

    def notify(self, message: str) -> None:
        self.message = message
        self.message_time = 2.1

    def _text(self, target: pygame.Surface, text: str, pos: tuple[int, int],
              color=TEXT, font: pygame.font.Font | None = None) -> None:
        target.blit((font or self.font).render(text, True, color), pos)

    def _button(self, target: pygame.Surface, rect: pygame.Rect, label: str, active: bool) -> None:
        fill = (70, 117, 83) if active else PANEL_LIGHT
        pygame.draw.rect(target, fill, rect, border_radius=7)
        pygame.draw.rect(target, ACCENT if active else (76, 88, 88), rect, 1, border_radius=7)
        rendered = self.font.render(label, True, TEXT)
        target.blit(rendered, rendered.get_rect(center=rect.center))

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Muda o pincel; retorna True se o clique atingiu um botão."""
        if self.solid_button.collidepoint(pos):
            self.brush_solid = True
            return True
        if self.free_button.collidepoint(pos):
            self.brush_solid = False
            return True
        return False

    def update(self, dt: float) -> None:
        self.message_time = max(0.0, self.message_time - dt)

    def draw(self, target: pygame.Surface, tile_map: TileMap) -> None:
        self._text(target, "Tiles automáticos", (GRID_X, 24), TEXT, self.title_font)
        self._text(target, "Bordas desacopladas · terreno com e sem colisão", (GRID_X, 61), MUTED)
        pygame.draw.line(target, (75, 88, 86), (GRID_X, 103), (SCREEN_W - GRID_X, 103), 1)
        self._text(target, "MAPA", (GRID_X, 113), MUTED, self.small_font)

        pygame.draw.rect(target, PANEL, (PANEL_X, GRID_Y, SCREEN_W - PANEL_X - 28, 584), border_radius=10)
        self._text(target, "Edição", (PANEL_X + 18, GRID_Y + 16), TEXT, self.title_font)
        self._text(target, "Pincel", (PANEL_X + 18, GRID_Y + 63), MUTED, self.small_font)
        self._button(target, self.solid_button, "Pedra · com colisão", self.brush_solid)
        self._button(target, self.free_button, "Grama · sem colisão", not self.brush_solid)

        self._text(target, "Controles", (PANEL_X + 18, GRID_Y + 202))
        controls = (
            "Clique esquerdo: pintar célula",
            "Clique direito: apagar colisão",
            "WASD / setas: mover personagem",
            "R: gerar mapa aleatório",
            "C: limpar mapa",
            "M: alternar pincel",
        )
        for index, line in enumerate(controls):
            self._text(target, line, (PANEL_X + 18, GRID_Y + 232 + index * 27), MUTED, self.small_font)

        self._text(target, f"Células sólidas: {tile_map.solid_count}", (PANEL_X + 18, GRID_Y + 422), ACCENT)
        self._text(target, "Borda automática", (PANEL_X + 18, GRID_Y + 454))
        self._text(target, "Cada lado compara o tipo da", (PANEL_X + 18, GRID_Y + 480), MUTED, self.small_font)
        self._text(target, "célula com o de sua vizinha.", (PANEL_X + 18, GRID_Y + 500), MUTED, self.small_font)
        self._text(target, "O personagem não atravessa", (PANEL_X + 18, GRID_Y + 530), MUTED, self.small_font)
        self._text(target, "células de pedra.", (PANEL_X + 18, GRID_Y + 550), MUTED, self.small_font)

        if self.message_time > 0:
            rendered = self.font.render(self.message, True, TEXT)
            box = rendered.get_rect(midbottom=(GRID_X + GRID_W // 2, GRID_Y + GRID_H - 12)).inflate(24, 14)
            pygame.draw.rect(target, (36, 47, 45), box, border_radius=7)
            target.blit(rendered, rendered.get_rect(center=box.center))
