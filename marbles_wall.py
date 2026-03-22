#!/usr/bin/env python3
import os, random, math
import pygame
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

# ---- WALL LAYOUT ----
COLS = 5
ROWS = 4  # 20 screens total

# ---- DISPLAY SETUP ----
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["DISPLAY"] = ":0.0"

pygame.display.init()
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

disp_info = pygame.display.Info()
width = disp_info.current_w
height = disp_info.current_h
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)

# ---- UNIVERSE (ENTIRE WALL) ----
universe_w = width * COLS
universe_h = height * ROWS

# ---- THIS TILE'S OFFSET (BASED ON RANK) ----
tile_x = rank % COLS
tile_y = rank // COLS
offset_x = tile_x * width
offset_y = tile_y * height

# ---- COLORS ----
BG = (0, 0, 0)
BALL_FILL = (220, 225, 235)
BALL_OUTLINE = (0, 0, 0)

# ---- "MARBLES IN A BUCKET" TUNING ----
N_BALLS = 90

# Bigger marbles
R_MIN, R_MAX = 40, 80

DT = 1.0
GRAVITY = 0.55
AIR_DAMP = 0.995
GROUND_DAMP = 0.85

SOLVER_ITERS = 6
MAX_SPEED = 35.0

# Bucket/container walls
LEFT_WALL = 0
RIGHT_WALL = universe_w

# ---- SPAWNING ----
POUR_WIDTH_FRAC = 0.10
SPAWN_TOP_RANGE = 900
JITTER = 0.12

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

if rank == 0:
    balls = []
    bucket_width = (RIGHT_WALL - LEFT_WALL)
    pour_center = (LEFT_WALL + RIGHT_WALL) // 2
    pour_width = int(bucket_width * POUR_WIDTH_FRAC)

    for _ in range(N_BALLS):
        r = random.randint(R_MIN, R_MAX)

        x0 = random.randint(pour_center - pour_width, pour_center + pour_width)
        x0 = max(LEFT_WALL + r, min(RIGHT_WALL - r, x0))

        y0 = random.randint(-SPAWN_TOP_RANGE, 0)

        balls.append({
            "x": float(x0),
            "y": float(y0),
            "vx": random.uniform(-1.0, 1.0),
            "vy": random.uniform(0.0, 3.0),
            "radius": r,
            "color": BALL_FILL,
        })
else:
    balls = None

running = True
while running:
    comm.Barrier()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ---- UPDATE ONLY ON RANK 0 ----
    if rank == 0:

        # Integrate motion
        for b in balls:
            b["vy"] += GRAVITY * DT
            b["vx"] += random.uniform(-JITTER, JITTER)

            b["vx"] = clamp(b["vx"], -MAX_SPEED, MAX_SPEED)
            b["vy"] = clamp(b["vy"], -MAX_SPEED, MAX_SPEED)

            b["x"] += b["vx"] * DT
            b["y"] += b["vy"] * DT

        # Air damping
        for b in balls:
            b["vx"] *= AIR_DAMP
            b["vy"] *= AIR_DAMP

        # Constraint solving
        for _ in range(SOLVER_ITERS):
            floor_y = universe_h

            # Walls + floor
            for b in balls:
                r = b["radius"]

                if b["x"] < LEFT_WALL + r:
                    b["x"] = LEFT_WALL + r
                    b["vx"] *= -0.25

                if b["x"] > RIGHT_WALL - r:
                    b["x"] = RIGHT_WALL - r
                    b["vx"] *= -0.25

                if b["y"] > floor_y - r:
                    b["y"] = floor_y - r
                    if b["vy"] > 0:
                        b["vy"] *= -0.05
                    b["vx"] *= GROUND_DAMP

            # Circle collisions
            for i in range(len(balls)):
                bi = balls[i]
                for j in range(i + 1, len(balls)):
                    bj = balls[j]

                    dx = bj["x"] - bi["x"]
                    dy = bj["y"] - bi["y"]
                    min_dist = bi["radius"] + bj["radius"]

                    dist2 = dx*dx + dy*dy
                    if dist2 == 0:
                        dx = random.uniform(-1, 1)
                        dy = random.uniform(-1, 1)
                        dist2 = dx*dx + dy*dy

                    if dist2 < (min_dist * min_dist):
                        dist = math.sqrt(dist2)
                        nx = dx / dist
                        ny = dy / dist
                        overlap = (min_dist - dist)

                        # Separate
                        bi["x"] -= nx * overlap * 0.5
                        bi["y"] -= ny * overlap * 0.5
                        bj["x"] += nx * overlap * 0.5
                        bj["y"] += ny * overlap * 0.5

                        # Small velocity tweak
                        bi["vx"] -= nx * overlap * 0.02
                        bi["vy"] -= ny * overlap * 0.02
                        bj["vx"] += nx * overlap * 0.02
                        bj["vy"] += ny * overlap * 0.02

        state = balls
    else:
        state = None

    # Broadcast
    balls = comm.bcast(state, root=0)

    # ---- DRAW ----
    screen.fill(BG)

    for b in balls:
        local_x = int(b["x"] - offset_x)
        local_y = int(b["y"] - offset_y)

        if -200 <= local_x <= width + 200 and -200 <= local_y <= height + 200:
            r = int(b["radius"])
            pygame.draw.circle(screen, b["color"], (local_x, local_y), r, 0)
            pygame.draw.circle(screen, BALL_OUTLINE, (local_x, local_y), r, 3)

    pygame.display.update()
    clock.tick(30)
