"""Character drawing, done with shapes so the game ships without image files.

Coordinates follow a 64x64 design grid (the same one as the mockups) and are
scaled to the requested size.
"""

import pygame

GREEN = (124, 255, 107)
ORANGE = (255, 159, 67)
INK = (11, 16, 32)
WHITE = (255, 255, 255)

TROGGLE_POINTS = [
    (32, 4), (40, 14), (54, 10), (52, 24), (62, 32), (52, 40), (54, 54), (40, 50),
    (32, 60), (24, 50), (10, 54), (12, 40), (2, 32), (12, 24), (10, 10), (24, 14),
]


class _Pen:
    def __init__(self, surf, center, size):
        self.surf = surf
        self.s = size / 64
        self.ox = center[0] - size / 2
        self.oy = center[1] - size / 2

    def p(self, x, y):
        return (self.ox + x * self.s, self.oy + y * self.s)

    def r(self, v):
        return max(1, round(v * self.s))

    def circle(self, color, x, y, r):
        pygame.draw.circle(self.surf, color, self.p(x, y), self.r(r))

    def ellipse(self, color, cx, cy, rx, ry):
        x, y = self.p(cx - rx, cy - ry)
        pygame.draw.ellipse(self.surf, color, (x, y, 2 * rx * self.s, 2 * ry * self.s))

    def rect(self, color, x, y, w, h):
        px, py = self.p(x, y)
        pygame.draw.rect(self.surf, color, (px, py, w * self.s, h * self.s))

    def poly(self, color, points):
        pygame.draw.polygon(self.surf, color, [self.p(x, y) for x, y in points])

    def line(self, color, a, b, w):
        pygame.draw.line(self.surf, color, self.p(*a), self.p(*b), self.r(w))


def _mouth_curve(y_top, depth, steps=12):
    """Bottom curve of the mouth, from (14, y_top) to (50, y_top)."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier with control point (32, y_top + depth)
        x = (1 - t) ** 2 * 14 + 2 * (1 - t) * t * 32 + t ** 2 * 50
        y = (1 - t) ** 2 * y_top + 2 * (1 - t) * t * (y_top + depth) + t ** 2 * y_top
        pts.append((x, y))
    return pts


def draw_muncher(surf, center, size, mood="happy", color=GREEN):
    """mood: happy (mouth open), chomp (mouth shut), sad (X eyes), cheer."""
    pen = _Pen(surf, center, size)
    pen.ellipse(color, 32, 38, 26, 22)
    pen.circle(color, 22, 18, 9)
    pen.circle(color, 42, 18, 9)

    if mood == "sad":
        for x in (22, 42):
            pen.line(INK, (x - 5, 13), (x + 5, 23), 3)
            pen.line(INK, (x + 5, 13), (x - 5, 23), 3)
        frown = [(20 + i * 2, 48 - 8 * (1 - ((i - 6) / 6) ** 2)) for i in range(13)]
        pygame.draw.lines(surf, INK, False, [pen.p(*q) for q in frown], pen.r(4))
        return

    if mood == "cheer":
        for x in (22, 42):
            arc = [(x - 6 + i, 20 - 6 * (1 - ((i - 6) / 6) ** 2)) for i in range(13)]
            pygame.draw.lines(surf, INK, False, [pen.p(*q) for q in arc], pen.r(3))
    else:
        for x in (22, 42):
            pen.circle(WHITE, x, 17, 5)
            pen.circle(INK, x + 1, 18, 2.5)

    if mood == "chomp":
        pen.line(INK, (16, 42), (48, 42), 3)
        return
    pen.poly(INK, [(14, 38)] + _mouth_curve(38, 22) + [(50, 38)])
    pen.rect(WHITE, 24, 38, 5, 5)
    pen.rect(WHITE, 35, 38, 5, 5)


def draw_troggle(surf, center, size, color=ORANGE):
    pen = _Pen(surf, center, size)
    pen.poly(color, TROGGLE_POINTS)
    for x in (24, 40):
        pen.circle(WHITE, x, 29, 5)
    pen.circle(INK, 25, 30, 2.5)
    pen.circle(INK, 39, 30, 2.5)
    pen.line(INK, (17, 20), (30, 25), 3)
    pen.line(INK, (47, 20), (34, 25), 3)
    pen.rect(INK, 22, 41, 20, 5)


def make_icon(size=64):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    draw_muncher(surf, (size / 2, size / 2), size)
    return surf
