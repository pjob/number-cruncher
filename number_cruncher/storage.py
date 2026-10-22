"""High scores and remembered settings, kept in the user's data directory."""

import json
import os
from pathlib import Path

MAX_SCORES = 10


def data_dir():
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "number-cruncher"


class Storage:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_dir() / "save.json"
        self.scores = []
        self.settings = {}
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text())
            self.scores = [s for s in data.get("scores", []) if isinstance(s, dict)][:MAX_SCORES]
            self.settings = dict(data.get("settings", {}))
        except (OSError, ValueError, AttributeError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"scores": self.scores, "settings": self.settings}, indent=2))
            tmp.replace(self.path)
        except OSError:
            pass  # Losing a high score is not worth crashing the game over.

    def qualifies(self, score):
        if score <= 0:
            return False
        return len(self.scores) < MAX_SCORES or score > self.scores[-1]["score"]

    def add_score(self, name, score, mode, level):
        """Insert a score and return its index in the table, or None."""
        entry = {"name": name, "score": score, "mode": mode, "level": level}
        self.scores.append(entry)
        self.scores.sort(key=lambda s: s["score"], reverse=True)
        self.scores = self.scores[:MAX_SCORES]
        self.save()
        for i, s in enumerate(self.scores):
            if s is entry:
                return i
        return None
