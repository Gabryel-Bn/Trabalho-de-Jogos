"""Utilitários compartilhados pelo jogo."""
from collections import defaultdict
import pygame


class EventBus:
    """Canal de comunicação entre objetos sem referências diretas."""
    def __init__(self): self._listeners = defaultdict(list)
    def subscribe(self, event_name, callback): self._listeners[event_name].append(callback)
    def emit(self, event_name, **payload):
        for callback in tuple(self._listeners[event_name]): callback(**payload)


def circles_overlap(first, second):
    return first.position.distance_squared_to(second.position) <= (first.radius + second.radius) ** 2


def clamp_position(position, radius, width, height):
    position.x = max(radius, min(width - radius, position.x))
    position.y = max(radius, min(height - radius, position.y))
    return position


def draw_bar(surface, position, size, value, maximum, color):
    ratio = max(0, min(1, value / maximum))
    outer = pygame.Rect(position, size)
    pygame.draw.rect(surface, (24, 28, 42), outer, border_radius=4)
    inner = outer.copy(); inner.width = int(outer.width * ratio)
    pygame.draw.rect(surface, color, inner, border_radius=4)
