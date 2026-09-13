from abc import ABC, abstractmethod
import pygame
from bullet import Projectile
from util import clamp_position, draw_bar
from assets import load_ship


class Player:
    """Contexto do State Pattern: cada estado controla dano e power-up."""
    def __init__(self, position, bus, width, height):
        self.position, self.bus = pygame.Vector2(position), bus
        self.width, self.height = width, height
        self.radius, self.health, self.max_health = 18, 100, 100
        self.speed, self.fire_cooldown, self.fire_timer = 260, .18, 0
        self.upgrades = {"weapon": 0, "boots": 0, "armor": 0}
        self.aim, self.state = pygame.Vector2(1, 0), NormalState(self)
        self.sprite = load_ship()
        bus.subscribe("player_damaged", self.take_damage)
        bus.subscribe("powerup_collected", self.activate_powerup)

    def change_state(self, state_type, duration=0): self.state = state_type(self, duration)
    def update(self, dt, keys, mouse_position):
        movement = pygame.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        if movement.length_squared(): self.position += movement.normalize() * self.speed * dt
        clamp_position(self.position, self.radius, self.width, self.height)
        mouse_vector = pygame.Vector2(mouse_position) - self.position
        if mouse_vector.length_squared(): self.aim = mouse_vector.normalize()
        self.fire_timer = max(0, self.fire_timer - dt); self.state.update(dt)

    def shoot(self):
        if self.fire_timer == 0:
            self.fire_timer = self.fire_cooldown
            self.bus.emit("projectile_spawned", projectile=Projectile(self.position + self.aim * 24, self.aim, "player", self.bus))

    def take_damage(self, amount):
        if self.state.can_take_damage:
            self.health -= amount; self.bus.emit("screen_shake", intensity=7); self.change_state(InvincibleState, 1.0)
            if self.health <= 0: self.bus.emit("player_died")

    def activate_powerup(self, kind):
        if kind == "rapid": self.change_state(RapidFireState, 6)
        elif kind == "heal": self.health = min(self.max_health, self.health + 35)

    def apply_upgrade(self, kind):
        """Upgrades permanentes escolhidos entre ondas."""
        self.upgrades[kind] += 1
        if kind == "weapon":
            self.fire_cooldown = max(.045, self.fire_cooldown * .78)
        elif kind == "boots":
            self.speed += 42
        elif kind == "armor":
            self.max_health += 25
            self.health = min(self.max_health, self.health + 25)

    def draw(self, surface):
        # O sprite original aponta para cima; a rotação acompanha a mira.
        angle = self.aim.angle_to(pygame.Vector2(0, -1))
        sprite = pygame.transform.rotate(self.sprite, angle)
        surface.blit(sprite, sprite.get_rect(center=self.position))
        pygame.draw.line(surface, (245, 249, 255), self.position, self.position + self.aim * 28, 3)
        draw_bar(surface, (18, 52), (180, 14), self.health, self.max_health, (86, 220, 128))


class PlayerState(ABC):
    color, can_take_damage = (67, 180, 255), True
    def __init__(self, player, duration=0): self.player, self.time_left = player, duration
    @abstractmethod
    def update(self, dt): pass

class NormalState(PlayerState):
    def update(self, dt): pass

class InvincibleState(PlayerState):
    color, can_take_damage = (255, 235, 97), False
    def update(self, dt):
        self.time_left -= dt
        if self.time_left <= 0: self.player.change_state(NormalState)

class RapidFireState(PlayerState):
    color = (192, 100, 255)
    def __init__(self, player, duration):
        super().__init__(player, duration); self.previous_cooldown = player.fire_cooldown; player.fire_cooldown = .075
    def update(self, dt):
        self.time_left -= dt
        if self.time_left <= 0:
            self.player.fire_cooldown = self.previous_cooldown; self.player.change_state(NormalState)
