"""Screens (scenes) and the main loop."""

import argparse
import random
import sys

import pygame

from . import __version__, rules
from .sound import Sounds
from .sprites import GREEN, ORANGE, draw_muncher, draw_troggle, make_icon
from .storage import Storage

W, H = 960, 720
FPS = 60

BG = (11, 16, 32)
PANEL = (20, 27, 51)
BORDER = (42, 53, 96)
TEXT = (232, 240, 255)
MUTED = (143, 163, 199)
YELLOW = (255, 209, 102)
GREEN_BG = (26, 42, 26)
EMPTY_BG = (14, 20, 40)
EMPTY_BORDER = (26, 34, 64)
TROGGLE_BG = (42, 30, 20)
DIM_LIFE = (42, 53, 96)

START_LIVES = 3
MAX_LIVES = 5
MODAL_MIN_AGE = 0.4  # seconds before a popup can be dismissed (stops key-mashing)

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
MOVES = {
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
}


# --- Text helpers ----------------------------------------------------------

FONT_PATHS = {
    True: "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    False: "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
}
_fonts = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        try:
            _fonts[key] = pygame.font.Font(FONT_PATHS[bold], size)
        except (OSError, FileNotFoundError):
            _fonts[key] = pygame.font.SysFont("dejavusansmono,monospace", size, bold=bold)
    return _fonts[key]


def draw_text(surf, text, size, color, pos, anchor="topleft", bold=True):
    img = font(size, bold).render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def fit_size(text, max_width, sizes, bold=True):
    for size in sizes:
        if font(size, bold).size(text)[0] <= max_width:
            return size
    return sizes[-1]


def wrap(text, size, width, bold=False):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if font(size, bold).size(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def panel(surf, rect, fill=PANEL, border=BORDER, width=2, radius=10):
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, width, border_radius=radius)


def dim(surf, alpha=200):
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    shade.fill((5, 8, 18, alpha))
    surf.blit(shade, (0, 0))


def footer(surf, text, y=H - 30):
    draw_text(surf, text, 13, MUTED, (W // 2, y), "center")


# --- Game session ----------------------------------------------------------

class Session:
    """Everything that carries over from one level to the next."""

    def __init__(self, mode, grade):
        self.mode = mode
        self.grade = grade
        self.level = 1
        self.score = 0
        self.lives = START_LIVES
        self.rng = random.Random()
        self.puzzle = self.new_puzzle()

    def new_puzzle(self):
        return rules.make_puzzle(self.mode, self.grade, self.level, self.rng)

    def points_per_munch(self):
        return 10 + 5 * self.level


class Scene:
    wants_text = False

    def __init__(self, app):
        self.app = app

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


# --- Title -----------------------------------------------------------------

class TitleScene(Scene):
    MODE_BOX = pygame.Rect(64, 258, 532, 64)
    GRADE_BOX = pygame.Rect(628, 258, 130, 48)

    def __init__(self, app):
        super().__init__(app)
        settings = app.storage.settings
        self.mode = settings.get("mode", 0) % len(rules.MODES)
        self.grade = settings.get("grade", 1) % len(rules.GRADES)

    def mode_rect(self, i):
        return self.MODE_BOX.move(0, i * 74)

    def grade_rect(self, i):
        return self.GRADE_BOX.move((i % 2) * 138, (i // 2) * 56)

    def start(self):
        self.app.storage.settings.update(mode=self.mode, grade=self.grade)
        self.app.storage.save()
        session = Session(rules.MODES[self.mode], self.grade)
        self.app.switch(PlayScene(self.app, session))

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.mode = (self.mode - 1) % len(rules.MODES)
                self.app.sounds.play("select")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.mode = (self.mode + 1) % len(rules.MODES)
                self.app.sounds.play("select")
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.grade = (self.grade - 1) % len(rules.GRADES)
                self.app.sounds.play("select")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.grade = (self.grade + 1) % len(rules.GRADES)
                self.app.sounds.play("select")
            elif event.key in CONFIRM_KEYS:
                self.start()
            elif event.key == pygame.K_h:
                self.app.switch(ScoresScene(self.app))
            elif event.key == pygame.K_ESCAPE:
                self.app.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(rules.MODES)):
                if self.mode_rect(i).collidepoint(event.pos):
                    if i == self.mode:
                        self.start()
                    else:
                        self.mode = i
                        self.app.sounds.play("select")
            for i in range(len(rules.GRADES)):
                if self.grade_rect(i).collidepoint(event.pos):
                    self.grade = i
                    self.app.sounds.play("select")

    def draw(self, surf):
        surf.fill(BG)
        draw_muncher(surf, (150, 118), 112)
        draw_text(surf, "NUMBER", 50, GREEN, (232, 52))
        draw_text(surf, "CRUNCHER", 50, GREEN, (232, 108))
        draw_text(surf, "Munch the right numbers. Dodge the Troggles.", 20, MUTED, (232, 178), bold=False)

        draw_text(surf, "CHOOSE A GAME", 14, MUTED, (64, 230))
        for i, mode in enumerate(rules.MODES):
            r = self.mode_rect(i)
            selected = i == self.mode
            panel(surf, r, GREEN_BG if selected else PANEL, GREEN if selected else BORDER, radius=8)
            color = GREEN if selected else TEXT
            if selected:
                draw_text(surf, "►", 18, GREEN, (r.x + 16, r.centery), "midleft")
            draw_text(surf, mode.upper(), 19, color, (r.x + 48, r.y + 10))
            draw_text(surf, rules.MODE_EXAMPLES[mode], 17, MUTED, (r.x + 48, r.y + 36), bold=False)

        draw_text(surf, "DIFFICULTY", 14, MUTED, (628, 230))
        for i, grade in enumerate(rules.GRADES):
            r = self.grade_rect(i)
            selected = i == self.grade
            panel(surf, r, GREEN_BG if selected else BG, GREEN if selected else BORDER, radius=6)
            draw_text(surf, grade, 18, GREEN if selected else TEXT, r.center, "center", bold=selected)

        how = pygame.Rect(628, 376, 268, 214)
        panel(surf, how, radius=8)
        draw_text(surf, "HOW TO PLAY", 13, YELLOW, (how.x + 16, how.y + 14))
        y = how.y + 42
        for text, color in (
            ("Move with the arrow keys. Press SPACE to munch a number that fits the rule.", TEXT),
            ("Eat a wrong number or get caught by a Troggle and you lose a life.", ORANGE),
        ):
            for line in wrap(text, 15, how.w - 32):
                draw_text(surf, line, 15, color, (how.x + 16, y), bold=False)
                y += 20
            y += 10
        draw_text(surf, "H  HIGH SCORES ►", 13, GREEN, (628, 608))

        footer(surf, "↑↓ GAME   ←→ DIFFICULTY   ENTER START   M SOUND   F11 FULL SCREEN   ESC QUIT")


# --- Play ------------------------------------------------------------------

class Troggle:
    def __init__(self, kind, col, row, dc, dr, interval, moves):
        self.kind = kind
        self.col, self.row = col, row
        self.dc, self.dr = dc, dr
        self.interval = interval
        self.timer = interval
        self.moves_left = moves


class PlayScene(Scene):
    HUD = pygame.Rect(32, 22, 896, 88)
    GRID = pygame.Rect(32, 126, 896, 548)
    GAP = 8
    READY_TIME = 1.6
    WARN_TIME = 1.6

    def __init__(self, app, session):
        super().__init__(app)
        self.s = session
        self.puzzle = session.puzzle
        self.rng = session.rng
        self.board = rules.make_board(self.puzzle)
        self.muncher = [2, 2]
        self.troggles = []
        self.warnings = []  # [col, row, time_left, troggle_args]
        self.popups = []  # [x, y, text, time_left]
        self.modal = None
        self.modal_age = 0.0
        self.paused = False
        self.ready = self.READY_TIME
        self.clearing = None  # countdown to the level-clear screen
        self.elapsed = 0.0
        self.mistakes = 0
        self.munched = 0
        self.chomp = 0.0
        self.invulnerable = 0.0
        self.spawn_timer = max(3.0, 8.0 - session.level * 0.5)

        level, grade = session.level, session.grade
        self.max_troggles = min(1 + (level - 1) // 2, 4)
        self.troggle_interval = max(0.45, 1.6 - 0.1 * level - 0.08 * grade)
        self.kinds = ["straight"] + (["wander"] if level >= 2 else []) + (["chaser"] if level >= 4 else [])

    # -- helpers --

    def cell_rect(self, col, row):
        cw = (self.GRID.w - (rules.COLS - 1) * self.GAP) / rules.COLS
        ch = (self.GRID.h - (rules.ROWS - 1) * self.GAP) / rules.ROWS
        x = self.GRID.x + col * (cw + self.GAP)
        y = self.GRID.y + row * (ch + self.GAP)
        return pygame.Rect(round(x), round(y), round(cw), round(ch))

    def index(self, col, row):
        return row * rules.COLS + col

    def remaining(self):
        return sum(1 for item in self.board if item and item.correct)

    def frozen(self):
        return self.paused or self.modal or self.ready > 0 or self.clearing is not None

    # -- events --

    def handle(self, event):
        if event.type == pygame.WINDOWFOCUSLOST and not self.modal:
            self.paused = True
        if event.type != pygame.KEYDOWN:
            return
        key = event.key

        if self.paused:
            if key in (pygame.K_p, pygame.K_ESCAPE) + CONFIRM_KEYS:
                self.paused = False
            elif key == pygame.K_q:
                self.app.switch(TitleScene(self.app))
            return
        if self.modal:
            if key in CONFIRM_KEYS and self.modal_age >= MODAL_MIN_AGE:
                self.dismiss_modal()
            return
        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.paused = True
            return
        if self.ready > 0:
            self.ready = 0  # any key skips the "get ready" banner
            return
        if self.clearing is not None:
            return

        if key in MOVES:
            dc, dr = MOVES[key]
            c, r = self.muncher[0] + dc, self.muncher[1] + dr
            if 0 <= c < rules.COLS and 0 <= r < rules.ROWS:
                self.muncher = [c, r]
                self.app.sounds.play("move")
                self.check_collision()
        elif key in CONFIRM_KEYS:
            self.munch()

    def munch(self):
        i = self.index(*self.muncher)
        item = self.board[i]
        self.chomp = 0.18
        if item is None:
            return
        self.board[i] = None
        if item.correct:
            points = self.s.points_per_munch()
            self.s.score += points
            self.munched += 1
            rect = self.cell_rect(*self.muncher)
            self.popups.append([rect.centerx, rect.y + 10, f"+{points}", 0.8])
            self.app.sounds.play("munch")
            if self.remaining() == 0:
                self.clearing = 0.9
                self.app.sounds.play("clear")
        else:
            self.lose_life("oops", "OOPS!", *item.explanation)
            self.app.sounds.play("wrong")

    def lose_life(self, kind, title, headline, detail):
        self.s.lives -= 1
        self.mistakes += 1
        self.modal = {"kind": kind, "title": title, "headline": headline, "detail": detail}
        self.modal_age = 0.0

    def dismiss_modal(self):
        kind = self.modal["kind"]
        self.modal = None
        if self.s.lives <= 0:
            self.app.switch(GameOverScene(self.app, self.s))
            return
        self.invulnerable = 1.0
        if kind == "caught":
            self.troggles.clear()
            self.warnings.clear()
            self.spawn_timer = 3.0

    def check_collision(self):
        if self.modal or self.invulnerable > 0:
            return
        for t in self.troggles:
            if [t.col, t.row] == self.muncher:
                self.lose_life("caught", "CAUGHT!", "A Troggle got you.",
                               "Watch for the ! signs: Troggles are coming.")
                self.app.sounds.play("caught")
                return

    # -- simulation --

    def update(self, dt):
        for p in self.popups:
            p[1] -= 40 * dt
            p[3] -= dt
        self.popups = [p for p in self.popups if p[3] > 0]
        self.chomp = max(0.0, self.chomp - dt)

        if self.modal:
            self.modal_age += dt
            return
        if self.paused:
            return
        if self.ready > 0:
            self.ready -= dt
            return
        if self.clearing is not None:
            self.clearing -= dt
            if self.clearing <= 0:
                self.app.switch(LevelClearScene(self.app, self.s, self.munched, self.mistakes, self.elapsed))
            return

        self.elapsed += dt
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.update_spawns(dt)
        for t in list(self.troggles):
            t.timer -= dt
            if t.timer <= 0:
                t.timer = t.interval
                self.step_troggle(t)
        self.check_collision()

    def update_spawns(self, dt):
        for w in list(self.warnings):
            w[2] -= dt
            if w[2] <= 0:
                self.warnings.remove(w)
                self.troggles.append(Troggle(*w[3]))
        if len(self.troggles) + len(self.warnings) >= self.max_troggles:
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_timer = self.rng.uniform(3.0, 7.0) / (1 + 0.1 * self.s.level)

        # Enter from a random edge, heading inward, not right next to the player.
        for _ in range(10):
            side = self.rng.randrange(4)
            r, c = self.rng.randrange(rules.ROWS), self.rng.randrange(rules.COLS)
            col, row, dc, dr = [
                (0, r, 1, 0),
                (rules.COLS - 1, r, -1, 0),
                (c, 0, 0, 1),
                (c, rules.ROWS - 1, 0, -1),
            ][side]
            if abs(col - self.muncher[0]) + abs(row - self.muncher[1]) > 1:
                break
        kind = self.rng.choice(self.kinds)
        args = (kind, col, row, dc, dr, self.troggle_interval, self.rng.randint(8, 16))
        self.warnings.append([col, row, self.WARN_TIME, args])
        self.app.sounds.play("warn")

    def step_troggle(self, t):
        old = (t.col, t.row)
        if t.kind != "straight" and t.moves_left > 0:
            options = [(dc, dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= t.col + dc < rules.COLS and 0 <= t.row + dr < rules.ROWS]
            choice = None
            if t.kind == "chaser" and self.rng.random() < 0.75:
                dx = self.muncher[0] - t.col
                dy = self.muncher[1] - t.row
                if dx or dy:
                    if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and self.rng.random() < 0.5):
                        choice = (1 if dx > 0 else -1, 0)
                    else:
                        choice = (0, 1 if dy > 0 else -1)
            if choice is None:
                # Wander, avoiding an immediate U-turn when there's another way.
                forward = [o for o in options if o != (-t.dc, -t.dr)] or options
                choice = self.rng.choice(forward)
            t.dc, t.dr = choice
        t.col += t.dc
        t.row += t.dr
        t.moves_left -= 1

        if not (0 <= t.col < rules.COLS and 0 <= t.row < rules.ROWS):
            self.troggles.remove(t)
        # Troggles sometimes leave a fresh number behind them.
        i = self.index(*old)
        if self.board[i] is None and list(old) != self.muncher and self.rng.random() < 0.15:
            self.board[i] = self.puzzle.make_item(self.rng.random() < 0.4)

    # -- drawing --

    def draw(self, surf):
        surf.fill(BG)
        self.draw_hud(surf)
        self.draw_grid(surf)
        for x, y, text, life in self.popups:
            draw_text(surf, text, 24, GREEN, (x, y), "midtop")
        footer(surf, "ARROWS MOVE · SPACE MUNCH · P PAUSE", H - 24)
        draw_text(surf, f"LEFT TO FIND: {self.remaining()}", 13, MUTED, (928, H - 24), "midright")

        if self.ready > 0:
            self.draw_ready(surf)
        elif self.modal:
            self.draw_modal(surf)
        elif self.paused:
            dim(surf)
            draw_text(surf, "PAUSED", 48, YELLOW, (W // 2, H // 2 - 40), "center")
            draw_text(surf, "P  RESUME     Q  QUIT TO MENU", 16, TEXT, (W // 2, H // 2 + 30), "center")

    def draw_hud(self, surf):
        r = self.HUD
        panel(surf, r)
        draw_text(surf, f"LEVEL {self.s.level} · {self.s.mode.upper()}", 13, MUTED, (r.x + 24, r.y + 16))
        draw_text(surf, self.puzzle.title, 32, YELLOW, (r.x + 24, r.y + 38))

        lives_slots = max(START_LIVES, self.s.lives)
        lx = r.right - 24 - lives_slots * 32 + 4
        draw_text(surf, "LIVES", 13, MUTED, (r.right - 24, r.y + 16), "topright")
        for i in range(lives_slots):
            color = GREEN if i < self.s.lives else DIM_LIFE
            draw_muncher(surf, (lx + i * 32 + 14, r.y + 58), 28, "chomp", color)
        sx = lx - 40
        draw_text(surf, "SCORE", 13, MUTED, (sx, r.y + 16), "topright")
        draw_text(surf, f"{self.s.score:06,}", 26, TEXT, (sx, r.y + 40), "topright")

    def draw_grid(self, surf):
        warn_cells = {(w[0], w[1]) for w in self.warnings}
        troggle_cells = {(t.col, t.row) for t in self.troggles}
        blink = (pygame.time.get_ticks() // 250) % 2 == 0
        mc, mr = self.muncher
        cell_w = self.cell_rect(0, 0).w
        label_size = min((fit_size(item.label, cell_w - 16, [46, 40, 34, 28, 24, 20])
                          for item in self.board if item), default=46)

        for row in range(rules.ROWS):
            for col in range(rules.COLS):
                rect = self.cell_rect(col, row)
                item = self.board[self.index(col, row)]
                here = (col, row)
                is_muncher = here == (mc, mr)

                if is_muncher:
                    panel(surf, rect, GREEN_BG, GREEN, 3, 8)
                elif here in troggle_cells:
                    panel(surf, rect, TROGGLE_BG, ORANGE, 2, 8)
                elif item is None:
                    panel(surf, rect, EMPTY_BG, EMPTY_BORDER, 2, 8)
                else:
                    panel(surf, rect, PANEL, BORDER, 2, 8)
                if here in warn_cells and blink:
                    pygame.draw.rect(surf, ORANGE, rect, 3, border_radius=8)

                if is_muncher:
                    mood = "chomp" if self.chomp > 0 else "happy"
                    if self.invulnerable > 0 and blink:
                        mood = "chomp"
                    if item:
                        draw_muncher(surf, (rect.centerx, rect.y + 38), 58, mood)
                        size = fit_size(item.label, rect.w - 12, [20, 18, 16, 14])
                        draw_text(surf, item.label, size, TEXT, (rect.centerx, rect.bottom - 6), "midbottom")
                    else:
                        draw_muncher(surf, rect.center, 72, mood)
                elif here in troggle_cells:
                    draw_troggle(surf, rect.center, 72)
                elif item:
                    draw_text(surf, item.label, label_size, TEXT, rect.center, "center")
                if here in warn_cells and here not in troggle_cells and not is_muncher:
                    draw_text(surf, "!", 26, ORANGE, (rect.right - 14, rect.y + 6), "topright")

    def draw_ready(self, surf):
        dim(surf, 150)
        box = pygame.Rect(0, 0, 620, 190)
        box.center = (W // 2, H // 2)
        panel(surf, box, border=YELLOW, width=3, radius=14)
        draw_text(surf, f"LEVEL {self.s.level}", 18, MUTED, (box.centerx, box.y + 34), "center")
        size = fit_size(self.puzzle.title, box.w - 48, [44, 38, 32])
        draw_text(surf, self.puzzle.title, size, YELLOW, (box.centerx, box.y + 88), "center")
        draw_text(surf, "GET READY!", 18, GREEN, (box.centerx, box.y + 146), "center")

    def draw_modal(self, surf):
        dim(surf)
        m = self.modal
        box = pygame.Rect(0, 0, 600, 420)
        box.center = (W // 2, H // 2)
        panel(surf, box, border=ORANGE, width=3, radius=14)
        if m["kind"] == "caught":
            draw_troggle(surf, (box.centerx, box.y + 64), 88)
        else:
            draw_muncher(surf, (box.centerx, box.y + 64), 88, "sad")
        draw_text(surf, m["title"], 34, ORANGE, (box.centerx, box.y + 140), "center")
        size = fit_size(m["headline"], box.w - 48, [26, 22, 18], bold=False)
        draw_text(surf, m["headline"], size, TEXT, (box.centerx, box.y + 192), "center", bold=False)

        detail_size = fit_size(m["detail"], box.w - 80, [24, 20, 17, 15], bold=False)
        detail = font(detail_size, False).render(m["detail"], True, YELLOW)
        dbox = detail.get_rect().inflate(36, 24)
        dbox.center = (box.centerx, box.y + 246)
        panel(surf, dbox, BG, None, radius=8)
        surf.blit(detail, detail.get_rect(center=dbox.center))

        lives = self.s.lives
        left = "No lives left." if lives == 0 else f"You have {lives} {'life' if lives == 1 else 'lives'} left."
        draw_text(surf, left, 18, MUTED, (box.centerx, box.y + 300), "center", bold=False)
        ready = self.modal_age >= MODAL_MIN_AGE
        btn = pygame.Rect(0, 0, 320, 50)
        btn.center = (box.centerx, box.y + 360)
        pygame.draw.rect(surf, ORANGE if ready else BORDER, btn, border_radius=8)
        draw_text(surf, "SPACE TO CONTINUE", 16, BG, btn.center, "center")


# --- Between levels --------------------------------------------------------

class LevelClearScene(Scene):
    def __init__(self, app, session, munched, mistakes, elapsed):
        super().__init__(app)
        self.s = session
        self.age = 0.0
        self.cleared_level = session.level
        self.cleared_title = session.puzzle.title
        self.per = session.points_per_munch()
        self.munched = munched
        self.no_mistakes = 100 if mistakes == 0 else 0
        self.seconds = int(elapsed)
        self.time_bonus = max(0, 100 - self.seconds)
        session.score += self.no_mistakes + self.time_bonus
        self.bonus_life = session.level % 3 == 0 and session.lives < MAX_LIVES
        if self.bonus_life:
            session.lives += 1
        session.level += 1
        session.puzzle = session.new_puzzle()

    def handle(self, event):
        if event.type != pygame.KEYDOWN or self.age < MODAL_MIN_AGE:
            return
        if event.key in CONFIRM_KEYS:
            self.app.switch(PlayScene(self.app, self.s))
        elif event.key == pygame.K_ESCAPE:
            self.app.switch(GameOverScene(self.app, self.s, quit_early=True))

    def update(self, dt):
        self.age += dt

    def draw(self, surf):
        surf.fill(BG)
        draw_muncher(surf, (100, 88), 88, "cheer")
        draw_text(surf, f"LEVEL {self.cleared_level} CLEAR!", 40, GREEN, (164, 46))
        draw_text(surf, f"You found every one: {self.cleared_title}.", 20, MUTED, (164, 102), bold=False)

        box = pygame.Rect(56, 160, 504, 460)
        panel(surf, box)
        draw_text(surf, "SCORE", 14, MUTED, (box.x + 24, box.y + 22))
        rows = [
            (f"Numbers munched  {self.munched} × {self.per}", self.munched * self.per),
            ("No mistakes bonus", self.no_mistakes),
            (f"Time bonus  {self.seconds // 60}:{self.seconds % 60:02d}", self.time_bonus),
        ]
        y = box.y + 62
        for label, value in rows:
            draw_text(surf, label, 20, TEXT, (box.x + 24, y), bold=False)
            draw_text(surf, str(value), 20, TEXT, (box.right - 24, y), "topright", bold=False)
            y += 40
        pygame.draw.line(surf, BORDER, (box.x + 24, y + 4), (box.right - 24, y + 4), 2)
        draw_text(surf, "TOTAL", 24, YELLOW, (box.x + 24, y + 22))
        draw_text(surf, f"{self.s.score:06,}", 24, YELLOW, (box.right - 24, y + 22), "topright")
        if self.bonus_life:
            draw_text(surf, "BONUS LIFE!", 18, GREEN, (box.x + 24, y + 70))

        nxt = pygame.Rect(box.x + 20, box.bottom - 136, box.w - 40, 116)
        panel(surf, nxt, BG, None, radius=8)
        draw_text(surf, f"UP NEXT · LEVEL {self.s.level}", 13, MUTED, (nxt.x + 18, nxt.y + 16))
        draw_text(surf, self.s.puzzle.title, 26, YELLOW, (nxt.x + 18, nxt.y + 40))
        draw_text(surf, "Watch out: the Troggles get faster.", 15, MUTED, (nxt.x + 18, nxt.y + 82), bold=False)

        draw_score_table(surf, pygame.Rect(588, 160, 316, 460), self.app.storage.scores[:8], compact=True)
        footer(surf, "ENTER NEXT LEVEL     ESC END GAME")


def draw_score_table(surf, box, scores, highlight=None, compact=False):
    panel(surf, box)
    if compact:
        draw_text(surf, "HIGH SCORES", 14, MUTED, (box.x + 24, box.y + 22))
    if not scores:
        top = box.y + (62 if compact else 28)
        for i, line in enumerate(wrap("No scores yet. Go munch some numbers!", 18, box.w - 48)):
            draw_text(surf, line, 18, TEXT, (box.x + 24, top + i * 24), bold=False)
        return
    y = box.y + (58 if compact else 24)
    for i, s in enumerate(scores):
        row = pygame.Rect(box.x + 14, y - 4, box.w - 28, 34)
        color = TEXT
        if i == highlight:
            pygame.draw.rect(surf, GREEN_BG, row, border_radius=6)
            color = GREEN
        draw_text(surf, f"{i + 1:>2}.", 20, color, (box.x + 22, y), bold=False)
        draw_text(surf, s["name"], 20, color, (box.x + 72, y))
        if not compact:
            draw_text(surf, f"{s['mode']}  L{s['level']}", 18, MUTED if i != highlight else GREEN,
                      (box.x + 190, y + 2), bold=False)
        draw_text(surf, f"{s['score']:06,}", 20, color, (box.right - 24, y), "topright", bold=False)
        y += 38 if not compact else 44


# --- Game over and scores --------------------------------------------------

class GameOverScene(Scene):
    def __init__(self, app, session, quit_early=False):
        super().__init__(app)
        self.s = session
        self.quit_early = quit_early
        self.age = 0.0
        self.entering = app.storage.qualifies(session.score)
        self.wants_text = self.entering
        self.name = ""

    def handle(self, event):
        if event.type != pygame.KEYDOWN or self.age < MODAL_MIN_AGE:
            return
        if self.entering:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                name = self.name or "???"
                idx = self.app.storage.add_score(name, self.s.score, self.s.mode, self.s.level)
                self.app.switch(ScoresScene(self.app, idx))
            elif event.unicode and event.unicode.isalnum() and event.unicode.isascii() and len(self.name) < 3:
                self.name += event.unicode.upper()
                self.app.sounds.play("select")
        elif event.key in CONFIRM_KEYS + (pygame.K_ESCAPE,):
            self.app.switch(ScoresScene(self.app))

    def update(self, dt):
        self.age += dt

    def draw(self, surf):
        surf.fill(BG)
        if self.quit_early:
            draw_muncher(surf, (W // 2, 130), 120, "happy")
            draw_text(surf, "THANKS FOR PLAYING", 40, GREEN, (W // 2, 240), "center")
        else:
            draw_muncher(surf, (W // 2, 130), 120, "sad")
            draw_text(surf, "GAME OVER", 52, ORANGE, (W // 2, 240), "center")
        draw_text(surf, f"Final score  {self.s.score:06,}", 26, TEXT, (W // 2, 310), "center")
        draw_text(surf, f"{self.s.mode} · {rules.GRADES[self.s.grade]} · reached level {self.s.level}",
                  18, MUTED, (W // 2, 350), "center", bold=False)

        if self.entering:
            draw_text(surf, "NEW HIGH SCORE! TYPE YOUR INITIALS", 16, GREEN, (W // 2, 420), "center")
            box = pygame.Rect(0, 0, 240, 72)
            box.center = (W // 2, 488)
            panel(surf, box, BG, GREEN, 3, 10)
            shown = self.name + ("_" if len(self.name) < 3 and (pygame.time.get_ticks() // 400) % 2 else " ")
            draw_text(surf, " ".join(shown.ljust(3)), 36, GREEN, box.center, "center")
            footer(surf, "ENTER SAVE     BACKSPACE DELETE")
        else:
            footer(surf, "ENTER CONTINUE")


class ScoresScene(Scene):
    def __init__(self, app, highlight=None):
        super().__init__(app)
        self.highlight = highlight

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS + (pygame.K_ESCAPE, pygame.K_h):
            self.app.switch(TitleScene(self.app))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.app.switch(TitleScene(self.app))

    def draw(self, surf):
        surf.fill(BG)
        draw_muncher(surf, (W // 2 - 230, 70), 72, "cheer")
        draw_text(surf, "HIGH SCORES", 44, YELLOW, (W // 2 + 40, 70), "center")
        draw_score_table(surf, pygame.Rect(150, 130, 660, 440), self.app.storage.scores, self.highlight)
        footer(surf, "ENTER BACK TO MENU")


# --- App -------------------------------------------------------------------

class App:
    def __init__(self, fullscreen=False):
        pygame.init()
        pygame.display.set_caption("Number Cruncher")
        pygame.display.set_icon(make_icon())
        flags = pygame.SCALED | pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((W, H), flags)
        self.clock = pygame.time.Clock()
        self.storage = Storage()
        self.sounds = Sounds(muted=self.storage.settings.get("muted", False))
        self.scene = TitleScene(self)
        self.running = True

    def switch(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and not self.scene.wants_text:
                    self.sounds.muted = not self.sounds.muted
                    self.storage.settings["muted"] = self.sounds.muted
                    self.storage.save()
                else:
                    self.scene.handle(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            if self.sounds.muted and not isinstance(self.scene, GameOverScene):
                draw_text(self.screen, "SOUND OFF (M)", 11, MUTED, (W - 10, H - 10), "bottomright")
            pygame.display.flip()
        pygame.quit()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="number-cruncher", description="Munch the numbers that fit the rule.")
    parser.add_argument("--fullscreen", action="store_true", help="start in full screen (F11 toggles)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    App(fullscreen=args.fullscreen).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
