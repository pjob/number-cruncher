import random
import re
import unittest

from number_cruncher import rules


def evaluate(text):
    """Evaluate an expression label like '12 ÷ 4' using exact integer math."""
    m = re.fullmatch(r"(\d+)(?: ([+−×÷]) (\d+))?", text)
    assert m, f"unexpected label {text!r}"
    a = int(m.group(1))
    if not m.group(2):
        return a
    b = int(m.group(3))
    op = m.group(2)
    if op == "+":
        return a + b
    if op == "−":
        return a - b
    if op == "×":
        return a * b
    assert a % b == 0, f"{text} does not divide evenly"
    return a // b


class BoardTests(unittest.TestCase):
    def boards(self):
        rng = random.Random(1234)
        for mode in rules.MODES:
            for grade in range(len(rules.GRADES)):
                for level in range(1, 8):
                    puzzle = rules.make_puzzle(mode, grade, level, rng)
                    yield mode, puzzle, rules.make_board(puzzle)

    def test_board_shape(self):
        for mode, puzzle, board in self.boards():
            self.assertEqual(len(board), rules.COLS * rules.ROWS)
            n_correct = sum(item.correct for item in board)
            self.assertTrue(8 <= n_correct <= 12, (mode, n_correct))

    def test_correctness_matches_rule(self):
        for mode, puzzle, board in self.boards():
            for item in board:
                v = evaluate(item.label)
                if mode == "Multiples":
                    expected = v % puzzle.k == 0
                elif mode == "Factors":
                    expected = puzzle.n % v == 0
                elif mode == "Primes":
                    expected = rules.is_prime(v)
                elif mode == "Equality":
                    expected = v == puzzle.target
                else:
                    expected = v < puzzle.target if puzzle.less else v > puzzle.target
                self.assertEqual(item.correct, expected, (puzzle.title, item.label))
                self.assertGreaterEqual(v, 0, item.label)

    def test_wrong_items_explain_themselves(self):
        for mode, puzzle, board in self.boards():
            for item in board:
                if item.correct:
                    self.assertIsNone(item.explanation)
                else:
                    headline, detail = item.explanation
                    self.assertIn(item.label, headline)
                    self.assertTrue(detail)


class ExplanationTests(unittest.TestCase):
    def test_multiples_brackets_the_number(self):
        p = rules.Multiples(random.Random(0), 1, 1)
        p.k = 7
        p.rng = random.Random(0)
        while True:
            item = p.make_item(False)
            if item.label == "27":
                break
        self.assertEqual(item.explanation, ("27 is not a multiple of 7.", "7 × 3 = 21   7 × 4 = 28"))

    def test_prime_explanation_shows_factors(self):
        p = rules.Primes(random.Random(0), 1, 1)
        p.composites = [21]
        self.assertEqual(p.make_item(False).explanation, ("21 is not prime.", "21 = 3 × 7"))

    def test_is_prime(self):
        self.assertEqual([n for n in range(20) if rules.is_prime(n)], [2, 3, 5, 7, 11, 13, 17, 19])


if __name__ == "__main__":
    unittest.main()
