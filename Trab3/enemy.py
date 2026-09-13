from abc import ABC, abstractmethod
import pygame

from bullet import Projectile
from util import draw_bar
from assets import load_zombie


class Enemy:
    def __init__(self, position, player, bus):
        self.position = pygame.Vector2(position)
        self.player, self.bus = player, bus
        self.radius, self.health, self.max_health, self.speed = 17, 3, 3, 85
        self.alive = True
        self.state = ApproachingState(self)
        self.sprite = load_zombie()

    def change_state(self, state_type, duration=0):
        self.state = state_type(self, duration)

    def update(self, dt): self.state.update(dt)

    def hit(self, damage):
        if not self.alive: return
        self.health -= damage
        self.change_state(StunnedState, .28)
        self.bus.emit("screen_shake", intensity=3)
        if self.health <= 0:
            self.alive = False
            self.bus.emit("enemy_destroyed", enemy=self)
            self.bus.emit("object_destroyed", object=self)

    def draw(self, surface):
        surface.blit(self.sprite, self.sprite.get_rect(center=self.position))
        pygame.draw.circle(surface, self.state.color, self.position, self.radius + 3, 2)
        draw_bar(surface, (self.position.x - 18, self.position.y - 29), (36, 5), self.health, self.max_health, (255, 92, 105))


class EnemyState(ABC):
    color = (245, 87, 101)
    def __init__(self, enemy, duration=0): self.enemy, self.time_left = enemy, duration
    @abstractmethod
    def update(self, dt): pass


class ApproachingState(EnemyState):
    color = (245, 87, 101)
    def update(self, dt):
        direction = self.enemy.player.position - self.enemy.position
        distance = direction.length()
        if distance: self.enemy.position += direction.normalize() * self.enemy.speed * dt
        if distance < 235: self.enemy.change_state(AimingState, .55)


class AimingState(EnemyState):
    color = (255, 170, 70)
    def update(self, dt):
        self.time_left -= dt
        if self.time_left <= 0:
            direction = self.enemy.player.position - self.enemy.position
            if direction.length_squared():
                self.enemy.bus.emit("projectile_spawned", projectile=Projectile(self.enemy.position, direction, "enemy", self.enemy.bus))
            self.enemy.change_state(ApproachingState)


class StunnedState(EnemyState):
    color = (102, 213, 255)
    def update(self, dt):
        self.time_left -= dt
        if self.time_left <= 0: self.enemy.change_state(ApproachingState)
