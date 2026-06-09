import os
import sys
import asyncio
import pygame
import random
import math

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

print('Inicializando pygame...')
pygame.init()
pygame.display.init()
pygame.font.init()
try:
    pygame.mixer.init()
except Exception:
    print('No se pudo iniciar el mezclador de sonido; continuando sin audio.')

# ----------------- CANVAS CONFIG -----------------
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Grammar Quest - Zelda RPG")
print('Pantalla inicializada', WIDTH, HEIGHT)

clock = pygame.time.Clock()

# ----------------- SCALE SYSTEM -----------------
BASE_W, BASE_H = 1000, 700
scale = min(WIDTH / BASE_W, HEIGHT / BASE_H)

def fsize(x):
    return max(12, int(x * scale))

# ----------------- FUENTES -----------------
font = pygame.font.SysFont("verdana", fsize(28))
big_font = pygame.font.SysFont("verdana", fsize(60), bold=True)
hud_font = pygame.font.SysFont("arial", fsize(38))

# ----------------- COLORES -----------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ----------------- SONIDOS -----------------
try:
    correct_sound = pygame.mixer.Sound("correct.wav")
except:
    correct_sound = None

try:
    wrong_sound = pygame.mixer.Sound("wrong.wav")
except:
    wrong_sound = None

# ----------------- TEXTO CENTRADO -----------------
def draw_center_text(text, font, color, y):
    surf = font.render(text, True, color)
    x = (WIDTH - surf.get_width()) // 2
    screen.blit(surf, (x, y))

# ----------------- FONDO -----------------
def draw_forest(surface):
    top = (20, 90, 50)
    bottom = (5, 25, 10)

    for y in range(HEIGHT):
        r = top[0] + (bottom[0] - top[0]) * (y / HEIGHT)
        g = top[1] + (bottom[1] - top[1]) * (y / HEIGHT)
        b = top[2] + (bottom[2] - top[2]) * (y / HEIGHT)
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (WIDTH, y))

# ----------------- PANEL BONITO (NUEVO) -----------------
def draw_question_panel(surface, rect):
    # sombra
    shadow = rect.copy()
    shadow.x += 8
    shadow.y += 8
    pygame.draw.rect(surface, (0, 0, 0, 120), shadow, border_radius=25)

    # base transparente
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (255, 255, 255, 235), panel.get_rect(), border_radius=25)

    # borde exterior
    pygame.draw.rect(panel, (40, 40, 40), panel.get_rect(), 4, border_radius=25)

    # borde interno estilo "fantasy"
    pygame.draw.rect(panel, (180, 180, 180), panel.get_rect(), 1, border_radius=25)

    surface.blit(panel, rect.topleft)

# ----------------- CORAZONES -----------------
def make_heart(color):
    size = int(32 * scale)
    size = max(16, size)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    pattern = [
        "01100110",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
        "00011000",
        "00000000"
    ]

    cell = size // 8

    for y, row in enumerate(pattern):
        for x, c in enumerate(row):
            if c == "1":
                pygame.draw.rect(surf, color, (x * cell, y * cell, cell, cell))

    return surf

heart_full = make_heart((220, 40, 40))
heart_empty = make_heart((70, 70, 70))

# ----------------- PREGUNTAS -----------------
questions = [
    {
        "question": "Choose the correct sentence:",
        "answers": [
            "I have been to London last year.",
            "I went to London last year.",
            "I go to London last year.",
            "I was go to London last year."
        ],
        "correct": 1
    },
    {
        "question": "If I _____ rich, I would travel the world.",
        "answers": ["am", "was", "were", "be"],
        "correct": 2
    },
    {
        "question": "What is a synonym of HAPPY?",
        "answers": ["Angry", "Joyful", "Sad", "Tired"],
        "correct": 1
    },
    {
        "question": "Choose correct passive voice:",
        "answers": [
            "The book was written by Shakespeare.",
            "Shakespeare wrote by the book.",
            "The book written Shakespeare.",
            "The book write Shakespeare."
        ],
        "correct": 0
    },
    {
        "question": "By next year I _____ my studies.",
        "answers": ["finish", "will finish", "will have finished", "finished"],
        "correct": 2
    },

    # EXTRA 10
    {
        "question": "Rarely have I seen such beauty:",
        "answers": [
            "I rarely seen it",
            "Rarely I have seen it",
            "Rarely have I seen it",
            "I have rarely saw it"
        ],
        "correct": 2
    },
    {
        "question": "She suggested that he ____ earlier.",
        "answers": ["go", "goes", "went", "had gone"],
        "correct": 0
    },
    {
        "question": "Reported speech: 'I am tired'",
        "answers": [
            "He said he is tired",
            "He said he was tired",
            "He said he will be tired",
            "He said he has tired"
        ],
        "correct": 1
    },
    {
        "question": "Relative clause:",
        "answers": [
            "The man which called you is here",
            "The man who called you is here",
            "The man that calling you is here",
            "The man whom calls you is here"
        ],
        "correct": 1
    },
    {
        "question": "She is used to ____ early.",
        "answers": ["wake", "waking", "wokes", "woke"],
        "correct": 1
    },
    {
        "question": "Modal deduction:",
        "answers": [
            "He must left",
            "He must have left",
            "He must to leave",
            "He must leaving"
        ],
        "correct": 1
    },
    {
        "question": "If I had studied harder, I ____ the exam.",
        "answers": ["would pass", "would have passed", "will pass", "passed"],
        "correct": 1
    },
    {
        "question": "Phrasal verb 'give up':",
        "answers": ["continue", "stop trying", "give away", "start again"],
        "correct": 1
    },
    {
        "question": "It is important that he ____ on time.",
        "answers": ["is", "be", "was", "will be"],
        "correct": 1
    }
]

random.shuffle(questions)

# ----------------- ESTADO -----------------
score = 0
lives = 3
max_lives = 3
question_index = 0
state = "menu"

TARGET_SCORE = 10

btn_w = int(700 * scale)
btn_h = int(70 * scale)
btn_x = WIDTH // 2 - btn_w // 2

buttons = [
    pygame.Rect(btn_x, int(220 * scale + i * (110 * scale)), btn_w, btn_h)
    for i in range(4)
]

start_btn = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 - 80, btn_w, btn_h)
quit_btn = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 40, btn_w, btn_h)

# ----------------- SHAKE -----------------
shake = 0

def add_shake(power=12):
    global shake
    shake = power

def get_shake():
    global shake
    if shake > 0:
        shake -= 1
        return (random.randint(-shake, shake), random.randint(-shake, shake))
    return (0, 0)

# ----------------- LOOP -----------------
async def main():
    global score, lives, question_index, state
    running = True

    while running:
        clock.tick(60)
        mouse = pygame.mouse.get_pos()
        ox, oy = get_shake()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:

                if state == "menu":
                    if start_btn.collidepoint(event.pos):
                        state = "game"
                    if quit_btn.collidepoint(event.pos):
                        running = False

                elif state == "game":
                    q = questions[question_index]

                    for i, b in enumerate(buttons):
                        if b.collidepoint(event.pos):

                            if i == q["correct"]:
                                score += 1
                                if correct_sound:
                                    correct_sound.play()
                            else:
                                lives -= 1
                                add_shake(15)
                                if wrong_sound:
                                    wrong_sound.play()

                            question_index += 1

                            if lives <= 0:
                                state = "lose"
                            elif score >= TARGET_SCORE:
                                state = "win"
                            elif question_index >= len(questions):
                                question_index = 0
                                random.shuffle(questions)

                elif state in ["win", "lose"]:
                    running = False

        # ----------------- BACKGROUND -----------------
        draw_forest(screen)

        # ----------------- MENU -----------------
        if state == "menu":
            draw_center_text("GRAMMAR QUEST", big_font, WHITE, int(HEIGHT * 0.25))

            pygame.draw.rect(screen, (30, 30, 30), start_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE, start_btn, 2, border_radius=12)

            pygame.draw.rect(screen, (30, 30, 30), quit_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE, quit_btn, 2, border_radius=12)

            draw_center_text("START", font, WHITE, start_btn.y + start_btn.height//4)
            draw_center_text("QUIT", font, WHITE, quit_btn.y + quit_btn.height//4)

        # ----------------- GAME -----------------
        elif state == "game":
            q = questions[question_index]

            panel = pygame.Rect(
                WIDTH//2 - int(450*scale),
                int(70*scale),
                int(900*scale),
                int(600*scale)
            )

            draw_question_panel(screen, panel)

            # QUESTION TEXT CENTERED INSIDE PANEL
            q_surf = font.render(q["question"], True, BLACK)
            screen.blit(
                q_surf,
                (panel.centerx - q_surf.get_width() // 2, panel.y + int(30 * scale))
            )

            for i, b in enumerate(buttons):
                color = (255, 220, 120) if b.collidepoint(mouse) else (220, 220, 220)

                pygame.draw.rect(screen, color, b, border_radius=12)
                pygame.draw.rect(screen, BLACK, b, 2, border_radius=12)

                txt = font.render(q["answers"][i], True, BLACK)
                screen.blit(txt, (b.x + int(10 * scale), b.y + int(20 * scale)))

            score_txt = hud_font.render(f"Score: {score}/{TARGET_SCORE}", True, WHITE)
            screen.blit(score_txt, (int(20 * scale), int(20 * scale)))

            for i in range(max_lives):
                img = heart_full if i < lives else heart_empty
                screen.blit(img, (WIDTH - int(200*scale) + i * int(60*scale) + ox, int(20*scale) + oy))

        # ----------------- WIN -----------------
        elif state == "win":
            draw_center_text("YOU SAVED HYRULE!", big_font, (0, 255, 120), int(HEIGHT * 0.35))
            draw_center_text(f"Final Score: {score}", font, WHITE, int(HEIGHT * 0.5))

        # ----------------- LOSE -----------------
        elif state == "lose":
            draw_center_text("GAME OVER", big_font, (255, 60, 60), int(HEIGHT * 0.35))
            draw_center_text(f"Final Score: {score}", font, WHITE, int(HEIGHT * 0.5))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
