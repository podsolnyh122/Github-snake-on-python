import sys
import xml.etree.ElementTree as ET
import pygame
import requests

pygame.init()

ROWS = 7
COLS = 53
CELL_SIZE = 12
PADDING = 3
RADIUS = 2

GRID_WIDTH = COLS * (CELL_SIZE + PADDING) - PADDING
GRID_HEIGHT = ROWS * (CELL_SIZE + PADDING) - PADDING
MARGIN_X = 30
MARGIN_Y = 30
SCREEN_WIDTH = GRID_WIDTH + MARGIN_X * 2
SCREEN_HEIGHT = GRID_HEIGHT + MARGIN_Y * 2 + 40

BG_COLOR = (1, 4, 9)
COLOR_L0 = (22, 27, 34)
COLOR_L1 = (14, 68, 41)
COLOR_L2 = (0, 109, 50)
COLOR_L3 = (38, 166, 65)
COLOR_L4 = (57, 211, 83)
SNAKE_COLOR = (138, 0, 143)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("GitHub Contribution Snake")
clock = pygame.time.Clock()

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

level_colors = {
    0: COLOR_L0,
    1: COLOR_L1,
    2: COLOR_L2,
    3: COLOR_L3,
    4: COLOR_L4
}

def fetch_contributions(username):
    grid = [[0 for _ in range(ROWS)] for _ in range(COLS)]
    url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=last"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json().get("contributions", [])
            for item in data[-371:]:
                day_idx = data.index(item)
                col = day_idx // 7
                row = day_idx % 7
                if col < COLS and row < ROWS:
                    grid[col][row] = item.get("level", 0)
            return grid
    except Exception:
        pass

    try:
        res = requests.get(f"https://github.com/users/{username}/contributions", timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            days = root.findall(".//td[@data-level]")
            for idx, d in enumerate(days[-371:]):
                col = idx // 7
                row = idx % 7
                if col < COLS and row < ROWS:
                    grid[col][row] = int(d.attrib.get("data-level", 0))
            return grid
    except Exception:
        pass

    return grid

username = input("Username: ").strip()
grid = fetch_contributions(username)

def grid_to_screen(col, row):
    return MARGIN_X + col * (CELL_SIZE + PADDING), MARGIN_Y + row * (CELL_SIZE + PADDING)

def reset_game(initial_grid):
    start_x, start_y = COLS // 2, ROWS // 2
    body = [
        [start_x, start_y],
        [start_x - 1, start_y],
        [start_x - 2, start_y],
        [start_x - 3, start_y]
    ]
    prev_body = [list(pos) for pos in body]
    g = [col[:] for col in initial_grid]
    for seg in body:
        g[seg[0]][seg[1]] = 0
    return body, prev_body, RIGHT, RIGHT, g, 0

body, prev_body, direction, next_direction, current_grid, score = reset_game(grid)

STEP_TIME = 0.10
step_timer = 0.0

while True:
    dt = clock.tick(60) / 1000.0
    step_timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w) and direction != DOWN:
                next_direction = UP
            elif event.key in (pygame.K_DOWN, pygame.K_s) and direction != UP:
                next_direction = DOWN
            elif event.key in (pygame.K_LEFT, pygame.K_a) and direction != RIGHT:
                next_direction = LEFT
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and direction != LEFT:
                next_direction = RIGHT
            elif event.key == pygame.K_r:
                body, prev_body, direction, next_direction, current_grid, score = reset_game(grid)
                step_timer = 0.0

    if step_timer >= STEP_TIME:
        step_timer -= STEP_TIME
        direction = next_direction
        prev_body = [list(pos) for pos in body]

        new_head = [body[0][0] + direction[0], body[0][1] + direction[1]]

        if (new_head[0] < 0 or new_head[0] >= COLS or
            new_head[1] < 0 or new_head[1] >= ROWS or
            new_head in body[:-1]):
            body, prev_body, direction, next_direction, current_grid, score = reset_game(grid)
            step_timer = 0.0
            continue

        body.insert(0, new_head)
        hx, hy = new_head

        if current_grid[hx][hy] > 0:
            score += current_grid[hx][hy]
            current_grid[hx][hy] = 0
            prev_body.append(list(prev_body[-1]))
        else:
            body.pop()

    t = min(1.0, step_timer / STEP_TIME)

    screen.fill(BG_COLOR)

    for c in range(COLS):
        for r in range(ROWS):
            x, y = grid_to_screen(c, r)
            val = current_grid[c][r]
            pygame.draw.rect(screen, level_colors[val], (x, y, CELL_SIZE, CELL_SIZE), border_radius=RADIUS)

    length = len(body)
    for i in range(length):
        curr_x, curr_y = body[i]
        prev_x, prev_y = prev_body[i]

        interp_x = prev_x + (curr_x - prev_x) * t
        interp_y = prev_y + (curr_y - prev_y) * t

        screen_x, screen_y = grid_to_screen(interp_x, interp_y)

        scale = max(0.48, 1.0 - (i / max(length, 1)) * 0.52)
        size = CELL_SIZE * scale
        offset = (CELL_SIZE - size) / 2

        rect = pygame.Rect(screen_x + offset, screen_y + offset, size, size)
        pygame.draw.rect(screen, SNAKE_COLOR, rect, border_radius=RADIUS)

    total_levels = sum(sum(col) for col in grid)
    consumed = score
    ratio = consumed / total_levels if total_levels > 0 else 1.0
    bar_width = int(GRID_WIDTH * min(1.0, ratio))

    bar_y = MARGIN_Y + GRID_HEIGHT + 24
    pygame.draw.rect(screen, COLOR_L1, pygame.Rect(MARGIN_X, bar_y, GRID_WIDTH, 9), border_radius=RADIUS)
    if bar_width > 0:
        pygame.draw.rect(screen, COLOR_L4, pygame.Rect(MARGIN_X, bar_y, bar_width, 9), border_radius=RADIUS)

    pygame.display.flip()