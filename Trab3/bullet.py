import pygame


class Projectile:
    """Projétil criado pelo evento projectile_spawned."""
    def __init__(self, position, direction, owner, bus):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(direction).normalize() * (680 if owner == "player" else 330)
        self.owner, self.bus = owner, bus
        self.radius = 5 if owner == "player" else 7
        self.damage = 1 if owner == "player" else 12
        self.life, self.alive = (1.25 if owner == "player" else 2.8), True

    def update(self, dt, width, height):
        self.position += self.velocity * dt; self.life -= dt
        if self.life <= 0 or not (-30 < self.position.x < width + 30 and -30 < self.position.y < height + 30): self.destroy()

    def destroy(self):
        if self.alive:
            self.alive = False; self.bus.emit("object_destroyed", object=self)

    def draw(self, surface):
        pygame.draw.circle(surface, (112, 230, 255) if self.owner == "player" else (255, 109, 118), self.position, self.radius)
