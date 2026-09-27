import math
import random
import pygame
from collision import Collide


pygame.init()
W, H = 800, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pinball")
clock = pygame.time.Clock()
title_font = pygame.font.SysFont("arial", 25, bold=True)
ui_font = pygame.font.SysFont("arial", 19, bold=True)
small_font = pygame.font.SysFont("arial", 15)

INK = (30, 24, 20)
FELT = (24, 89, 59)
GRID = (39, 111, 75)
WHITE = (248, 239, 208)
MINT = (231, 195, 111)
GOLD = (255, 205, 74)
CORAL = (192, 54, 61)
BLUE = (71, 144, 177)
PURPLE = (223, 172, 68)


def unit(v):
    length = math.hypot(v[0], v[1])
    return (v[0] / length, v[1] / length) if length else (0.0, 0.0)


def regular(center, radius, sides=16, phase=-math.pi / 2):
    return [(center[0] + math.cos(phase + i * math.tau / sides) * radius,
             center[1] + math.sin(phase + i * math.tau / sides) * radius)
            for i in range(sides)]


def flipper(pivot, length, angle, thickness=15):
    d = (math.cos(angle), math.sin(angle))
    n = (-d[1] * thickness / 2, d[0] * thickness / 2)
    tip = (pivot[0] + d[0] * length, pivot[1] + d[1] * length)
    return [(pivot[0] + n[0], pivot[1] + n[1]),
            (tip[0] + n[0] * .58, tip[1] + n[1] * .58),
            (tip[0] - n[0] * .58, tip[1] - n[1] * .58),
            (pivot[0] - n[0], pivot[1] - n[1])]


def reflect(poly, point, velocity, restitution=1.9, min_kick=70):
    """Resolve a polygon hit using its nearest edge normal."""
    best_distance, normal = float("inf"), (0.0, -1.0)
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        edge = (b[0] - a[0], b[1] - a[1])
        n = unit((-edge[1], edge[0]))
        signed = (point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1]
        if signed < 0:
            n = (-n[0], -n[1])
            signed = -signed
        if signed < best_distance:
            best_distance, normal = signed, n
    dot = velocity[0] * normal[0] + velocity[1] * normal[1]
    if dot < 0:
        velocity[0] -= (1 + restitution) * dot * normal[0]
        velocity[1] -= (1 + restitution) * dot * normal[1]
        dot = velocity[0] * normal[0] + velocity[1] * normal[1]
    # Garante uma velocidade mínima saindo da superfície. Sem isso, a bola
    # pode ficar "quicando fraquinho" pra sempre presa entre dois rails
    # bem próximos (como o cantinho perto do dreno direito), já que a
    # restituição das rails é < 1 e vai perdendo energia a cada toque.
    if dot < min_kick:
        boost = min_kick - dot
        velocity[0] += boost * normal[0]
        velocity[1] += boost * normal[1]
    return normal


def bounce_off_circle(center, radius, ball, restitution=1.65, min_kick=260):
    """Trata o bumper como um círculo de verdade na física (ele já é
    desenhado como círculo). Evita a normal instável que o SAT por aresta
    produzia quando a bola batia bem no centro do bumper."""
    dx = ball["x"] - center[0]
    dy = ball["y"] - center[1]
    dist = math.hypot(dx, dy)
    normal = (dx / dist, dy / dist) if dist else (0.0, -1.0)

    # Pequeno ruído na direção da normal. Sem isso, uma bola que cai
    # perfeitamente alinhada com o centro do bumper (sem nenhuma velocidade
    # horizontal) entra num loop vertical perfeito e determinístico: sobe
    # reto, bate no teto, desce reto, bate no bumper nesse mesmo eixo, pra
    # sempre. Bola real nunca bate tão simétrica assim.
    jitter = random.uniform(-0.05, 0.05)
    cos_j, sin_j = math.cos(jitter), math.sin(jitter)
    normal = (
        normal[0] * cos_j - normal[1] * sin_j,
        normal[0] * sin_j + normal[1] * cos_j,
    )

    speed_along_normal = ball["vx"] * normal[0] + ball["vy"] * normal[1]
    if speed_along_normal < 0:
        ball["vx"] -= (1 + restitution) * speed_along_normal * normal[0]
        ball["vy"] -= (1 + restitution) * speed_along_normal * normal[1]
        speed_along_normal = ball["vx"] * normal[0] + ball["vy"] * normal[1]

    # Garante um "pop" mínimo em qualquer contato, mesmo de raspão (ângulo
    # quase tangente). Sem isso, um toque de raspão dá um empurrão fraco
    # demais, a gravidade traz a bola de volta, e ela fica "vibrando"
    # grudada na borda do bumper em vez de sair de verdade.
    if speed_along_normal < min_kick:
        boost = min_kick - speed_along_normal
        ball["vx"] += boost * normal[0]
        ball["vy"] += boost * normal[1]

    # Reposiciona a bola exatamente na borda do círculo (+ folga), garantindo
    # que ela sempre saia de dentro do bumper, não importa a profundidade
    # da penetração no frame anterior.
    target = radius + ball["r"] + 1
    ball["x"] = center[0] + normal[0] * target
    ball["y"] = center[1] + normal[1] * target
    return normal


# Polygon side rails form a trapezoid and guide the ball away from the corners.
rails = [
    [(88, 570), (104, 572), (164, 105), (148, 105)],
    [(696, 572), (712, 570), (652, 105), (636, 105)],
    # Inward slanted guides feed the ball toward the flippers.
    [(122, 459), (134, 450), (251, 526), (242, 539)],
    [(678, 459), (666, 450), (549, 526), (558, 539)],
    # Ceiling: fecha a abertura de topo do feltro (antes era só um risco
    # decorativo). Sem isso a bola escapa por cima quando um bumper manda
    # ela pra cima com força.
    [(148, 88), (636, 88), (636, 100), (148, 100)],
]

# Velocidade máxima permitida pra bola (evita "explosão" de velocidade
# quando a bola fica presa/encostada numa forma por vários sub-passos
# seguidos e recebe impulso de restituição repetidas vezes).
MAX_SPEED = 900

# Triangular slingshots reflect the ball and make the lower playfield read as pinball.
slingshots = [
    [(130, 421), (253, 465), (221, 510)],
    [(670, 421), (547, 465), (579, 510)],
]

bumpers = [
    {"center": (330, 190), "radius": 34, "points": regular((330, 190), 34), "color": CORAL, "value": 500},
    {"center": (470, 190), "radius": 34, "points": regular((470, 190), 34), "color": BLUE, "value": 500},
    {"center": (400, 275), "radius": 38, "points": regular((400, 275), 38), "color": GOLD, "value": 1000},
]

# Three small polygon target inserts score on contact without redirecting the ball.
score_zones = [
    {"points": [(325, 365), (345, 355), (351, 394), (331, 399)], "value": 250, "color": PURPLE, "name": "250"},
    {"points": [(390, 359), (410, 359), (414, 398), (386, 398)], "value": 250, "color": PURPLE, "name": "250"},
    {"points": [(455, 365), (475, 355), (469, 399), (449, 394)], "value": 250, "color": PURPLE, "name": "250"},
]

score = 0
balls_left = 3
ball = None
trail = []
active_zones = set()
active_bumpers = set()
game_over = False


def launch_ball():
    global ball, balls_left, trail, active_zones, active_bumpers, game_over
    if ball is None and balls_left > 0:
        balls_left -= 1
        # Lança do canto inferior direito, como um plunger real, com um
        # tiro diagonal pra cima e pra esquerda dentro da mesa.
        # Entra pela lateral direita, numa faixa livre de obstáculos (acima
        # dos slingshots/guias, abaixo dos bumpers), correndo pra dentro
        # da mesa em vez de subir apertada pelo cantinho do flipper.
        ball = {"x": 620.0, "y": 300.0, "vx": random.uniform(-260, -200), "vy": random.uniform(-60, 60), "r": 9}
        trail = []
        active_zones = set()
        active_bumpers = set()
        game_over = False


def draw_board(left_flipper, right_flipper, left_up, right_up):
    screen.fill(INK)
    # Score panel styled like a simple cabinet backglass.
    pygame.draw.rect(screen, (65, 39, 25), (35, 16, 730, 58), border_radius=5)
    pygame.draw.rect(screen, MINT, (35, 16, 730, 58), width=2, border_radius=5)
    screen.blit(title_font.render("PINBALL", True, WHITE), (52, 29))
    screen.blit(small_font.render("MESA DE JOGO", True, MINT), (54, 54))
    screen.blit(ui_font.render(f"PONTOS  {score:06d}", True, GOLD), (475, 35))
    screen.blit(ui_font.render(f"BOLAS  {balls_left}", True, WHITE), (665, 35))

    # Wooden cabinet, flat green playfield, and metal perimeter rails.
    cabinet = [(110, 82), (690, 82), (724, 602), (76, 602)]
    pygame.draw.polygon(screen, (93, 53, 30), cabinet)
    pygame.draw.polygon(screen, (176, 125, 67), cabinet, 6)
    felt = [(142, 105), (658, 105), (701, 579), (99, 579)]
    pygame.draw.polygon(screen, FELT, felt)
    pygame.draw.polygon(screen, (39, 131, 83), felt, 2)
    for y in range(135, 550, 65):
        t = (y - 105) / 474
        left_edge = round(142 - 43 * t + 12)
        right_edge = round(658 + 43 * t - 12)
        pygame.draw.line(screen, GRID, (left_edge, y), (right_edge, y), 1)

    # Marca o ponto do lançador, na lateral direita.
    pygame.draw.circle(screen, GOLD, (620, 300), 6)
    screen.blit(small_font.render("LANÇADOR", True, WHITE), (626, 293))

    # Irregular scoring zones are visually distinct from physical rails.
    for zone in score_zones:
        pygame.draw.polygon(screen, (*zone["color"],), zone["points"])
        pygame.draw.polygon(screen, WHITE, zone["points"], 2)
        center = (sum(p[0] for p in zone["points"]) // len(zone["points"]),
                  sum(p[1] for p in zone["points"]) // len(zone["points"]))
        label = small_font.render(zone["name"], True, INK)
        screen.blit(label, label.get_rect(center=center))

    # Physical rails and classic red triangular sling pieces.
    for rail in rails:
        pygame.draw.polygon(screen, (120, 102, 76), rail)
        pygame.draw.polygon(screen, (237, 215, 168), rail, 2)
    for sling in slingshots:
        pygame.draw.polygon(screen, (122, 35, 43), sling)
        pygame.draw.polygon(screen, CORAL, sling, 3)
        center = (sum(p[0] for p in sling) // 3, sum(p[1] for p in sling) // 3)
        pygame.draw.circle(screen, WHITE, center, 3)

    # Classic round bumpers with concentric rings.
    for bumper in bumpers:
        pygame.draw.circle(screen, (73, 43, 30), bumper["center"], bumper["radius"] + 5)
        pygame.draw.circle(screen, WHITE, bumper["center"], bumper["radius"], 4)
        pygame.draw.circle(screen, bumper["color"], bumper["center"], 22)
        pygame.draw.circle(screen, GOLD, bumper["center"], 13)
        pygame.draw.circle(screen, WHITE, bumper["center"], 5)
        value = small_font.render(str(bumper["value"]), True, WHITE)
        screen.blit(value, value.get_rect(center=(bumper["center"][0], bumper["center"][1] + 51)))

    # Drain markings and flippers.
    pygame.draw.line(screen, (29, 38, 33), (292, 581), (508, 581), 4)
    pygame.draw.polygon(screen, (238, 205, 120) if left_up else (225, 220, 196), left_flipper)
    pygame.draw.polygon(screen, (103, 76, 47), left_flipper, 2)
    pygame.draw.polygon(screen, (238, 205, 120) if right_up else (225, 220, 196), right_flipper)
    pygame.draw.polygon(screen, (103, 76, 47), right_flipper, 2)
    pygame.draw.circle(screen, GOLD, (290, 535), 8)
    pygame.draw.circle(screen, GOLD, (510, 535), 8)

    screen.blit(small_font.render("ESPAÇO: LANÇAR", True, WHITE), (205, 625))
    screen.blit(small_font.render("A / ←: ESQUERDA", True, MINT), (350, 625))
    screen.blit(small_font.render("D / →: DIREITA", True, MINT), (510, 625))
    screen.blit(small_font.render("R: REINICIAR", True, WHITE), (357, 650))


running = True
while running:
    dt = min(clock.tick(60) / 1000, 1 / 30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                launch_ball()
            elif event.key == pygame.K_r:
                score, balls_left, ball, game_over = 0, 3, None, False

    keys = pygame.key.get_pressed()
    left_up = keys[pygame.K_a] or keys[pygame.K_LEFT]
    right_up = keys[pygame.K_d] or keys[pygame.K_RIGHT]
    left_flipper = flipper((290, 535), 100, -0.12 if not left_up else -0.65, thickness=13)
    right_flipper = flipper((510, 535), 100, math.pi + 0.12 if not right_up else math.pi + 0.65, thickness=13)

    if ball is not None:
        speed = math.hypot(ball["vx"], ball["vy"])
        steps = max(1, min(10, math.ceil(speed * dt / 4)))
        h = dt / steps
        for _ in range(steps):
            ball["vy"] = min(ball["vy"] + 520 * h, 680)
            ball["x"] += ball["vx"] * h
            ball["y"] += ball["vy"] * h
            p = (ball["x"], ball["y"])
            ball_poly = regular(p, ball["r"], 12)

            for rail in rails:
                if Collide.convex(ball_poly, rail):
                    velocity = [ball["vx"], ball["vy"]]
                    n = reflect(rail, p, velocity, 0.84)
                    ball["vx"], ball["vy"] = velocity
                    ball["x"] += n[0] * (ball["r"] + 2)
                    ball["y"] += n[1] * (ball["r"] + 2)
                    p = (ball["x"], ball["y"])
                    ball_poly = regular(p, ball["r"], 12)

            for sling in slingshots:
                if Collide.convex(ball_poly, sling):
                    velocity = [ball["vx"], ball["vy"]]
                    n = reflect(sling, p, velocity, 1.25)
                    ball["vx"], ball["vy"] = velocity
                    if ball["vy"] > -250:
                        ball["vy"] = -310
                    ball["x"] += n[0] * (ball["r"] + 2)
                    ball["y"] += n[1] * (ball["r"] + 2)
                    ball_poly = regular((ball["x"], ball["y"]), ball["r"], 12)

            for i, bumper in enumerate(bumpers):
                if Collide.convex(ball_poly, bumper["points"]):
                    bounce_off_circle(bumper["center"], bumper["radius"], ball, 1.65)
                    score += bumper["value"]
                    ball_poly = regular((ball["x"], ball["y"]), ball["r"], 12)

            for i, paddle in enumerate((left_flipper, right_flipper)):
                raised = left_up if i == 0 else right_up
                if Collide.convex(ball_poly, paddle):
                    velocity = [ball["vx"], ball["vy"]]
                    n = reflect(paddle, p, velocity, 1.0 if raised else 0.82)
                    ball["vx"], ball["vy"] = velocity
                    if raised:
                        ball["vy"] = min(ball["vy"], -420)
                        ball["vx"] += -65 if i == 0 else 65
                    ball["x"] += n[0] * (ball["r"] + 2)
                    ball["y"] += n[1] * (ball["r"] + 2)
                    ball_poly = regular((ball["x"], ball["y"]), ball["r"], 12)

            for i, zone in enumerate(score_zones):
                if Collide.convex(ball_poly, zone["points"]):
                    velocity = [ball["vx"], ball["vy"]]
                    n = reflect(zone["points"], p, velocity, 0.5)
                    ball["vx"], ball["vy"] = velocity
                    ball["x"] += n[0] * (ball["r"] + 2)
                    ball["y"] += n[1] * (ball["r"] + 2)
                    ball_poly = regular((ball["x"], ball["y"]), ball["r"], 12)
                    if i not in active_zones:
                        score += zone["value"]
                        active_zones.add(i)

            # Trava de segurança: se a bola acumulou velocidade demais (ex.:
            # vários bumpers seguidos, cada um com restituição > 1), limita
            # a velocidade máxima pra ela nunca "voar" pra fora da tela.
            current_speed = math.hypot(ball["vx"], ball["vy"])
            if current_speed > MAX_SPEED:
                scale = MAX_SPEED / current_speed
                ball["vx"] *= scale
                ball["vy"] *= scale

        trail.append((round(ball["x"]), round(ball["y"])))
        trail = trail[-11:]
        if ball["y"] > 625:
            ball = None
            if balls_left == 0:
                game_over = True

    draw_board(left_flipper, right_flipper, left_up, right_up)
    for i, point in enumerate(trail):
        pygame.draw.circle(screen, (31 + i * 3, 93 + i * 8, 111 + i * 9), point, 2 + i // 4)
    if ball is not None:
        pos = (round(ball["x"]), round(ball["y"]))
        pygame.draw.circle(screen, (255, 245, 215), pos, ball["r"])
        pygame.draw.circle(screen, GOLD, pos, ball["r"], 2)
        pygame.draw.circle(screen, WHITE, (pos[0] - 3, pos[1] - 3), 2)
    if ball is None:
        if game_over:
            message = "FIM DE JOGO  •  pressione R para jogar novamente"
        else:
            message = "PRESSIONE ESPAÇO PARA LANÇAR"
        label = ui_font.render(message, True, GOLD if game_over else WHITE)
        screen.blit(label, label.get_rect(center=(400, 500)))

    pygame.display.flip()

pygame.quit()