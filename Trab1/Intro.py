import pygame
import random

pygame.init()
pygame.font.init()

font = pygame.font.Font(None, 50)
Nome = "Gabryel Cauã"

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

texto = font.render(Nome, True, (0, 0, 0))
rect = texto.get_rect(center=(WIDTH // 2, HEIGHT // 2))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

    screen.fill((30, 30, 30))

    pygame.draw.rect(screen, (255, 255, 255), rect)
    screen.blit(texto, rect)

    pygame.display.flip()