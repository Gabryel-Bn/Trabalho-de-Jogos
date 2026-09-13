"""Neon Siege — twin-stick shooter demonstrando States e Events."""
import random
import pygame
from enemy import Enemy
from player import Player
from util import EventBus, circles_overlap

WIDTH, HEIGHT = 960, 620


class Game:
    def __init__(self):
        pygame.init(); pygame.display.set_caption("Neon Siege — Twin Stick Shooter")
        self.screen, self.clock = pygame.display.set_mode((WIDTH, HEIGHT)), pygame.time.Clock()
        self.font, self.big_font = pygame.font.Font(None, 28), pygame.font.Font(None, 64)
        self.bus, self.running, self.game_over = EventBus(), True, False
        self.objects, self.enemies, self.projectiles = [], [], []
        self.score, self.spawn_timer, self.shake = 0, .8, 0
        self.next_upgrade_score, self.choosing_upgrade = 150, False
        self.upgrade_options = []
        self.player = Player((WIDTH / 2, HEIGHT / 2), self.bus, WIDTH, HEIGHT)
        self.objects.append(self.player); self._subscribe_events()

    def _subscribe_events(self):
        self.bus.subscribe("projectile_spawned", self.add_projectile)
        self.bus.subscribe("enemy_spawned", self.add_enemy)
        self.bus.subscribe("object_destroyed", self.remove_object)
        self.bus.subscribe("enemy_destroyed", self.enemy_destroyed)
        self.bus.subscribe("screen_shake", self.start_shake)
        self.bus.subscribe("player_died", self.end_game)

    def add_projectile(self, projectile): self.projectiles.append(projectile); self.objects.append(projectile)
    def add_enemy(self, enemy): self.enemies.append(enemy); self.objects.append(enemy)
    def remove_object(self, object):
        for collection in (self.objects, self.projectiles, self.enemies):
            if object in collection: collection.remove(object)
    def enemy_destroyed(self, enemy):
        self.score += 10
        if random.random() < .15: self.bus.emit("powerup_collected", kind=random.choice(("rapid", "heal")))
        if self.score >= self.next_upgrade_score:
            self.next_upgrade_score += 150
            self.choosing_upgrade = True
            self.upgrade_options = random.sample(("weapon", "boots", "armor"), 3)
    def start_shake(self, intensity): self.shake = max(self.shake, intensity)
    def end_game(self): self.game_over = True

    def spawn_enemy(self):
        side, margin = random.randrange(4), 45
        if side == 0: position = (random.randrange(WIDTH), -margin)
        elif side == 1: position = (WIDTH + margin, random.randrange(HEIGHT))
        elif side == 2: position = (random.randrange(WIDTH), HEIGHT + margin)
        else: position = (-margin, random.randrange(HEIGHT))
        self.bus.emit("enemy_spawned", enemy=Enemy(position, self.player, self.bus))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over: self.__init__()
            elif event.type == pygame.KEYDOWN and self.choosing_upgrade and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                selected = event.key - pygame.K_1
                self.player.apply_upgrade(self.upgrade_options[selected])
                self.choosing_upgrade = False

    def resolve_collisions(self):
        for projectile in tuple(self.projectiles):
            if not projectile.alive: continue
            if projectile.owner == "player":
                for enemy in tuple(self.enemies):
                    if circles_overlap(projectile, enemy):
                        self.bus.emit("collision", first=projectile, second=enemy)
                        enemy.hit(projectile.damage); projectile.destroy(); break
            elif circles_overlap(projectile, self.player):
                self.bus.emit("collision", first=projectile, second=self.player)
                self.bus.emit("player_damaged", amount=projectile.damage); projectile.destroy()
        for enemy in tuple(self.enemies):
            if circles_overlap(enemy, self.player):
                self.bus.emit("collision", first=enemy, second=self.player)
                self.bus.emit("player_damaged", amount=18)

    def update(self, dt):
        if self.game_over or self.choosing_upgrade: return
        keys, mouse = pygame.key.get_pressed(), pygame.mouse.get_pos()
        self.player.update(dt, keys, mouse)
        if pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]: self.player.shoot()
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy(); self.spawn_timer = max(.28, 1.05 - self.score / 1000)
        for object in tuple(self.objects):
            if object is self.player: continue
            if object in self.projectiles: object.update(dt, WIDTH, HEIGHT)
            else: object.update(dt)
        self.resolve_collisions(); self.shake = max(0, self.shake - 25 * dt)

    def draw(self):
        self.screen.fill((10, 13, 25))
        for x in range(0, WIDTH, 40): pygame.draw.line(self.screen, (17, 23, 41), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40): pygame.draw.line(self.screen, (17, 23, 41), (0, y), (WIDTH, y))
        for object in self.objects: object.draw(self.screen)
        self.screen.blit(self.font.render(f"SCORE  {self.score}", True, (225, 232, 255)), (18, 18))
        self.screen.blit(self.font.render("WASD mover • Mouse mirar/atirar • ESPAÇO atirar", True, (150, 163, 195)), (18, HEIGHT - 32))
        label = f"Estado: {type(self.player.state).__name__.replace('State', '')}"
        self.screen.blit(self.font.render(label, True, self.player.state.color), (18, 76))
        levels = self.font.render("Upgrades  |  Tiro: {}  Botas: {}  Armadura: {}".format(
            self.player.upgrades["weapon"], self.player.upgrades["boots"], self.player.upgrades["armor"]), True, (190, 200, 230))
        self.screen.blit(levels, (18, 105))
        if self.choosing_upgrade:
            panel = pygame.Rect(WIDTH // 2 - 270, HEIGHT // 2 - 110, 540, 220)
            pygame.draw.rect(self.screen, (25, 30, 52), panel, border_radius=14)
            pygame.draw.rect(self.screen, (120, 180, 255), panel, 2, border_radius=14)
            title = self.font.render("UPGRADE DISPONÍVEL — pressione 1, 2 ou 3", True, (240, 245, 255))
            self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))
            descriptions = {"weapon": "Tiro rápido: -22% recarga", "boots": "Botas: +42 velocidade", "armor": "Armadura: +25 vida máxima"}
            for index, option in enumerate(self.upgrade_options, 1):
                text = self.font.render(f"[{index}] {descriptions[option]}", True, (160, 220, 255))
                self.screen.blit(text, (WIDTH // 2 - 215, HEIGHT // 2 - 25 + (index - 1) * 38))
        if self.game_over:
            title = self.big_font.render("FIM DE JOGO", True, (255, 108, 125))
            restart = self.font.render("Pressione R para reiniciar", True, (235, 235, 245))
            self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            self.screen.blit(restart, restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000, .05)
            self.handle_events(); self.update(dt); self.draw()
        pygame.quit()


if __name__ == "__main__": Game().run()
