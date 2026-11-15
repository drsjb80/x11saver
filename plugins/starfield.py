"""Starfield flying toward the viewer."""
import random

import pygame

FPS = 60
NUM_STARS = 250
SPEED = 480          # depth units per second (was 8 per frame at 60 fps)
FOCAL = 400.0

_stars = None
_size = None


def _random_star(width, height, depth):
    return [random.randint(-width, width), random.randint(-height, height), depth]


def init(screen, size):
    global _stars, _size
    _size = size
    width, height = size
    _stars = [_random_star(width, height, random.randint(1, width))
              for _ in range(NUM_STARS)]


def render(screen, dt):
    width, height = _size
    screen.fill((0, 0, 0))

    for star in _stars:
        star[2] -= SPEED * dt
        if star[2] <= 0:
            star[:] = _random_star(width, height, width)
        k = FOCAL / star[2]
        px, py = int(star[0] * k + width / 2), int(star[1] * k + height / 2)
        if 0 <= px < width and 0 <= py < height:
            closeness = 1 - star[2] / width
            brightness = min(255, int(closeness * 255))
            size = max(1, int(closeness * 5))
            pygame.draw.circle(screen, (brightness, brightness, brightness), (px, py), size)


def shutdown():
    pass
