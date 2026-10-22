"""Tiny synthesized square-wave sound effects, so no audio files are needed."""

from array import array

import pygame

# name -> list of (frequency Hz, duration seconds); frequency 0 is a rest
EFFECTS = {
    "munch": [(660, 0.04), (990, 0.06)],
    "wrong": [(180, 0.12), (140, 0.2)],
    "caught": [(520, 0.08), (390, 0.08), (260, 0.08), (130, 0.2)],
    "clear": [(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.2)],
    "warn": [(880, 0.03), (0, 0.04), (880, 0.03)],
    "move": [(330, 0.015)],
    "select": [(740, 0.03)],
}


class Sounds:
    def __init__(self, muted=False):
        self.muted = muted
        self.sounds = {}
        try:
            pygame.mixer.init(22050, -16, 1, 512)
            rate, size, channels = pygame.mixer.get_init()
            if size != -16:
                return
            for name, notes in EFFECTS.items():
                self.sounds[name] = pygame.mixer.Sound(buffer=self._render(notes, rate, channels))
        except (pygame.error, TypeError):
            self.sounds = {}  # No audio device: play silently.

    @staticmethod
    def _render(notes, rate, channels, volume=0.18):
        amp = int(32767 * volume)
        samples = array("h")
        for freq, dur in notes:
            n = int(rate * dur)
            for i in range(n):
                if freq:
                    v = amp if (i * freq * 2 // rate) % 2 == 0 else -amp
                    # Short fade-out on each note to avoid clicks.
                    v = v * min(1.0, (n - i) / 200)
                else:
                    v = 0
                samples.extend([int(v)] * channels)
        return samples.tobytes()

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()
