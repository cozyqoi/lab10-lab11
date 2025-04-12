import pygame
import random
import psycopg2
import datetime

# Database connection
conn = psycopg2.connect(
    database="phonebook",
    user="postgres",
    password="S4j0A2b7",
    host="localhost",
    port="5432"
)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE)")
cur.execute("""
CREATE TABLE IF NOT EXISTS user_score (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    score INTEGER,
    level INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# User input
username = input("Enter username: ")
cur.execute("SELECT id FROM users WHERE username = %s", (username,))
row = cur.fetchone()
if row:
    user_id = row[0]
else:
    cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
    user_id = cur.fetchone()[0]
    conn.commit()

# Load previous progress
cur.execute("""
SELECT score, level
FROM user_score
WHERE user_id = %s
ORDER BY last_updated DESC
LIMIT 1
""", (user_id,))
row = cur.fetchone()
if row:
    score, speed = row[0], row[1] + 5
else:
    score, speed = 0, 8

def calculate_level(score):
    return score // 5 + 1

def save_progress():
    cur.execute(
        "INSERT INTO user_score (user_id, score, level) VALUES (%s, %s, %s)",
        (user_id, score, level)
    )
    conn.commit()

def show_scoreboard(limit=5):
    print("\n=== Best Score ===")
    cur.execute("""
        SELECT u.username, us.score, us.level, us.last_updated
        FROM user_score us
        JOIN users u ON u.id = us.user_id
        ORDER BY us.score DESC
        LIMIT %s
    """, (limit,))
    for username, sc, lv, ts in cur.fetchall():
        print(f"{ts:%Y-%m-%d %H:%M:%S} | {username:<10} | score={sc:<3} | level={lv}")
    print("="*30, "\n")

# Pygame initialization
pygame.init()
cell_size = 20
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")
font = pygame.font.SysFont('Arial', 25)
clock = pygame.time.Clock()

# Game variables
snake = [(width//2, height//2)]
direction = (cell_size, 0)
next_direction = direction
food = None
gold_food = None
gold_time = 0
walls = []
bombs = []
wall_margin = 0
level = calculate_level(score)
paused = False
running = True
game_over = False

def is_position_valid(pos, include_walls=True):
    x, y = pos
    if include_walls and level >= 2 and (x < wall_margin or x >= width - wall_margin or 
                                        y < wall_margin or y >= height - wall_margin):
        return False
    return (pos not in snake and 
            pos not in bombs and
            (not gold_food or pos != gold_food))

def create_food():
    attempts = 0
    max_attempts = 100
    while attempts < max_attempts:
        if level >= 2:
            min_x = wall_margin + cell_size
            max_x = width - wall_margin - cell_size
            min_y = wall_margin + cell_size
            max_y = height - wall_margin - cell_size
            x = random.randrange(min_x, max_x, cell_size)
            y = random.randrange(min_y, max_y, cell_size)
        else:
            x = random.randrange(0, width, cell_size)
            y = random.randrange(0, height, cell_size)
        pos = (x, y)
        if is_position_valid(pos, include_walls=False):
            return pos
        attempts += 1
    while True:
        x = random.randrange(0, width, cell_size)
        y = random.randrange(0, height, cell_size)
        pos = (x, y)
        if is_position_valid(pos):
            return pos

def create_walls():
    wall_list = []
    margin = wall_margin
    for x in range(margin, width - margin, cell_size):
        wall_list.append((x, margin))
        wall_list.append((x, height - margin - cell_size))
    for y in range(margin + cell_size, height - margin - cell_size, cell_size):
        wall_list.append((margin, y))
        wall_list.append((width - margin - cell_size, y))
    return wall_list

def create_bombs(count):
    bomb_list = []
    while len(bomb_list) < count:
        if level >= 2:
            min_x = wall_margin + cell_size
            max_x = width - wall_margin - cell_size
            min_y = wall_margin + cell_size
            max_y = height - wall_margin - cell_size
            x = random.randrange(min_x, max_x, cell_size)
            y = random.randrange(min_y, max_y, cell_size)
        else:
            x = random.randrange(0, width, cell_size)
            y = random.randrange(0, height, cell_size)
        pos = (x, y)
        if is_position_valid(pos):
            bomb_list.append(pos)
    return bomb_list

food = create_food()

while running:
    current_level = calculate_level(score)
    
    if current_level > level:
        level = current_level
        if level == 2:
            wall_margin = 0  # Стены на краю для уровня 2
        elif level > 2:
            wall_margin = min(100, 20 * (level - 2))  # Уменьшение с уровня 3
        
        if level >= 2:
            walls = create_walls()
        if level >= 3:
            bomb_count = 3 + (level - 3)
            bombs = create_bombs(bomb_count)
        food = create_food()
        if gold_food:
            gold_food = create_food()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_progress()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
                if paused:
                    show_scoreboard()
            elif event.key == pygame.K_r and game_over:
                snake = [(width//2, height//2)]
                direction = (cell_size, 0)
                next_direction = direction
                score = 0
                level = 1
                wall_margin = 0
                walls = []
                bombs = []
                food = create_food()
                gold_food = None
                game_over = False
                speed = 8
            if not paused and not game_over:
                if event.key == pygame.K_UP and direction != (0, cell_size):
                    next_direction = (0, -cell_size)
                elif event.key == pygame.K_DOWN and direction != (0, -cell_size):
                    next_direction = (0, cell_size)
                elif event.key == pygame.K_LEFT and direction != (cell_size, 0):
                    next_direction = (-cell_size, 0)
                elif event.key == pygame.K_RIGHT and direction != (-cell_size, 0):
                    next_direction = (cell_size, 0)

    if paused or game_over:
        screen.fill("#a8d8a8")
        if game_over:
            text = font.render("GAME OVER! Press R to restart", True, "red")
            screen.blit(text, (width//2 - 150, height//2))
        else:
            text = font.render("PAUSED", True, "black")
            screen.blit(text, (width//2 - 50, height//2))
        pygame.display.update()
        continue

    direction = next_direction
    head_x, head_y = snake[0]
    new_head = (head_x + direction[0], head_y + direction[1])
    snake.insert(0, new_head)

    if new_head == food:
        score += 1
        food = create_food()
        speed += 0.5
        if random.random() < 0.2:
            gold_food = create_food()
            gold_time = pygame.time.get_ticks()
    elif gold_food and new_head == gold_food:
        score += 3
        gold_food = None
        speed += 1
    else:
        snake.pop()

    if gold_food and pygame.time.get_ticks() - gold_time > 5000:
        gold_food = None

    if level < 2:
        x, y = new_head
        if x >= width: x = 0
        elif x < 0: x = width - cell_size
        if y >= height: y = 0
        elif y < 0: y = height - cell_size
        snake[0] = (x, y)

    if (snake[0][0] < 0 or snake[0][0] >= width or 
        snake[0][1] < 0 or snake[0][1] >= height or
        snake[0] in snake[1:] or 
        (level >= 2 and snake[0] in walls) or 
        (level >= 3 and snake[0] in bombs)):
        save_progress()
        game_over = True

    screen.fill("#a8d8a8")
    if level >= 2:
        for wall in walls:
            pygame.draw.rect(screen, "#5c4033", (*wall, cell_size, cell_size))
    if level >= 3:
        for bomb in bombs:
            pygame.draw.rect(screen, "#000000", (*bomb, cell_size, cell_size))
    for segment in snake:
        pygame.draw.rect(screen, "#2a5c2a", (*segment, cell_size, cell_size))
    pygame.draw.rect(screen, "#c62828", (*food, cell_size, cell_size))
    if gold_food:
        pygame.draw.rect(screen, "#f9d71c", (*gold_food, cell_size, cell_size))
    score_text = font.render(f"Score: {score} | Level: {level}", True, "black")
    screen.blit(score_text, (10, 10))

    pygame.display.update()
    clock.tick(int(speed))

pygame.quit()
cur.close()
conn.close()