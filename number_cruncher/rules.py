"""Puzzle rules: what goes in the grid, which cells are correct, and why.

Everything here is pure logic with no pygame dependency so it can be tested
on its own.
"""

from dataclasses import dataclass
import random

COLS = 6
ROWS = 5

MODES = ["Multiples", "Factors", "Primes", "Equality", "Inequality"]
GRADES = ["Grade 2", "Grade 3", "Grade 4", "Grade 5+"]

MODE_EXAMPLES = {
    "Multiples": "Multiples of 4 → 8, 12, 20...",
    "Factors": "Factors of 24 → 2, 3, 8...",
    "Primes": "Prime numbers → 7, 11, 13...",
    "Equality": "Equals 12 → 3×4, 20−8, 6+6...",
    "Inequality": "Less than 9 → 2+5, 16÷2...",
}


@dataclass
class Item:
    """One cell's contents. `explanation` is (headline, detail) when wrong."""

    label: str
    correct: bool
    explanation: tuple = None


class Puzzle:
    """A single rule, e.g. "Multiples of 7", that can make grid items."""

    title = ""

    def __init__(self, rng):
        self.rng = rng

    def make_item(self, correct):
        raise NotImplementedError


# --- Multiples -------------------------------------------------------------

class Multiples(Puzzle):
    # (smallest k, largest k, largest multiplier) per grade
    RANGES = [(2, 5, 10), (2, 9, 10), (3, 12, 12), (6, 15, 12)]

    def __init__(self, rng, grade, level):
        super().__init__(rng)
        lo, hi, self.max_mult = self.RANGES[grade]
        self.k = rng.randint(lo, min(hi, lo + 2 + level))
        self.title = f"Multiples of {self.k}"

    def make_item(self, correct):
        k = self.k
        if correct:
            return Item(str(k * self.rng.randint(1, self.max_mult)), True)
        while True:
            n = self.rng.randint(2, k * self.max_mult)
            if n % k:
                break
        m = n // k
        if m == 0:
            detail = f"{k} × 1 = {k}"
        else:
            detail = f"{k} × {m} = {k * m}   {k} × {m + 1} = {k * (m + 1)}"
        return Item(str(n), False, (f"{n} is not a multiple of {k}.", detail))


# --- Factors ---------------------------------------------------------------

class Factors(Puzzle):
    TARGETS = [
        [12, 16, 18, 20, 24],
        [24, 30, 36, 40, 48],
        [36, 48, 60, 72, 80],
        [60, 72, 84, 90, 96, 100, 120],
    ]

    def __init__(self, rng, grade, level):
        super().__init__(rng)
        self.n = rng.choice(self.TARGETS[grade])
        self.title = f"Factors of {self.n}"
        self.factors = [d for d in range(1, self.n + 1) if self.n % d == 0]
        self.others = [d for d in range(2, self.n) if self.n % d]

    def make_item(self, correct):
        if correct:
            return Item(str(self.rng.choice(self.factors)), True)
        d = self.rng.choice(self.others)
        q, r = divmod(self.n, d)
        return Item(str(d), False, (
            f"{d} is not a factor of {self.n}.",
            f"{self.n} ÷ {d} = {q} remainder {r}",
        ))


# --- Primes ----------------------------------------------------------------

def is_prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


class Primes(Puzzle):
    LIMITS = [30, 50, 100, 150]
    title = "Prime numbers"

    def __init__(self, rng, grade, level):
        super().__init__(rng)
        limit = self.LIMITS[grade]
        self.primes = [n for n in range(2, limit + 1) if is_prime(n)]
        self.composites = [n for n in range(1, limit + 1) if not is_prime(n)]

    def make_item(self, correct):
        if correct:
            return Item(str(self.rng.choice(self.primes)), True)
        n = self.rng.choice(self.composites)
        if n == 1:
            return Item("1", False, (
                "1 is not prime.",
                "A prime has exactly two factors: 1 and itself.",
            ))
        a = next(d for d in range(2, n) if n % d == 0)
        return Item(str(n), False, (f"{n} is not prime.", f"{n} = {a} × {n // a}"))


# --- Expressions (Equality / Inequality) -----------------------------------

OPS_BY_GRADE = [["+", "−"], ["+", "−", "×"], ["+", "−", "×", "÷"], ["+", "−", "×", "÷"]]


def make_expression(rng, value, ops):
    """Return text for an arithmetic expression that evaluates to `value`."""
    ops = list(ops)
    rng.shuffle(ops)
    for op in ops:
        if op == "+" and value >= 2:
            a = rng.randint(1, value - 1)
            return f"{a} + {value - a}"
        if op == "−":
            b = rng.randint(1, 12)
            return f"{value + b} − {b}"
        if op == "×":
            pairs = [(a, value // a) for a in range(2, value) if value % a == 0 and a <= 12]
            if pairs:
                a, b = rng.choice(pairs)
                return f"{a} × {b}"
        if op == "÷" and value >= 1:
            b = rng.randint(2, 9)
            return f"{value * b} ÷ {b}"
    b = rng.randint(1, 9)
    return f"{value + b} − {b}"


class Equality(Puzzle):
    TARGETS = [(5, 20), (6, 30), (12, 50), (20, 100)]

    def __init__(self, rng, grade, level):
        super().__init__(rng)
        self.target = rng.randint(*self.TARGETS[grade])
        self.ops = OPS_BY_GRADE[grade]
        self.title = f"Equals {self.target}"

    def make_item(self, correct):
        t = self.target
        if correct:
            return Item(make_expression(self.rng, t, self.ops), True)
        while True:
            v = t + self.rng.choice([-1, 1]) * self.rng.randint(1, 5)
            if v >= 1:
                break
        text = make_expression(self.rng, v, self.ops)
        return Item(text, False, (f"{text} is not equal to {t}.", f"{text} = {v}"))


class Inequality(Puzzle):
    TARGETS = [(6, 15), (8, 25), (12, 40), (20, 80)]

    def __init__(self, rng, grade, level):
        super().__init__(rng)
        self.target = rng.randint(*self.TARGETS[grade])
        self.ops = OPS_BY_GRADE[grade]
        self.less = rng.random() < 0.5
        self.title = f"Less than {self.target}" if self.less else f"Greater than {self.target}"

    def make_item(self, correct):
        t = self.target
        spread = max(6, t // 2)
        below = (max(1, t - spread), t - 1)
        above = (t + 1, t + spread)
        if correct:
            v = self.rng.randint(*(below if self.less else above))
            return Item(make_expression(self.rng, v, self.ops), True)
        # Wrong answers include the target itself: 9 is not less than 9.
        if self.less:
            v = self.rng.randint(t, above[1])
        else:
            v = self.rng.randint(below[0], t)
        text = make_expression(self.rng, v, self.ops)
        word = "less" if self.less else "greater"
        return Item(text, False, (f"{text} is not {word} than {t}.", f"{text} = {v}"))


PUZZLES = {
    "Multiples": Multiples,
    "Factors": Factors,
    "Primes": Primes,
    "Equality": Equality,
    "Inequality": Inequality,
}


def make_puzzle(mode, grade, level, rng=None):
    return PUZZLES[mode](rng or random.Random(), grade, level)


def make_board(puzzle):
    """Fill a COLS x ROWS grid. Returns a flat list of Items, row by row."""
    rng = puzzle.rng
    n_cells = COLS * ROWS
    n_correct = rng.randint(8, 12)
    items = []
    seen = set()
    for i in range(n_cells):
        correct = i < n_correct
        # Prefer distinct labels, but small pools (e.g. factors of 12) can't
        # always provide them.
        for _ in range(25):
            item = puzzle.make_item(correct)
            if item.label not in seen:
                break
        seen.add(item.label)
        items.append(item)
    rng.shuffle(items)
    return items
