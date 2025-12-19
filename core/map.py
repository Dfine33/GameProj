import random

PLAIN = '.'
MOUNTAIN = '#'
RIVER = '~'

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[PLAIN for _ in range(width)] for _ in range(height)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def can_walk(self, x, y):
        return self.in_bounds(x, y) and self.grid[y][x] == PLAIN

def generate(width=40, height=20):
    m = Map(width, height)
    half_w = width // 2
    noise = [[random.random() for _ in range(half_w)] for _ in range(height)]
    for _ in range(3):
        for y in range(height):
            for x in range(half_w):
                s = noise[y][x]
                c = 1
                if x > 0:
                    s += noise[y][x-1]; c += 1
                if x+1 < half_w:
                    s += noise[y][x+1]; c += 1
                if y > 0:
                    s += noise[y-1][x]; c += 1
                if y+1 < height:
                    s += noise[y+1][x]; c += 1
                noise[y][x] = s / c
    for y in range(height):
        for x in range(half_w):
            v = noise[y][x]
            if v > 0.72:
                m.grid[y][x] = MOUNTAIN
            elif v > 0.6 and random.random() < 0.5:
                m.grid[y][x] = MOUNTAIN
            else:
                m.grid[y][x] = PLAIN
    cx = half_w // 2
    ry = random.randint(height//3, height*2//3)
    for y in range(height):
        cx += random.choice([-1, 0, 1])
        cx = max(1, min(half_w-2, cx))
        m.grid[y][cx] = RIVER
        if random.random() < 0.5:
            m.grid[y][cx+1] = RIVER
    for y in range(height):
        for x in range(half_w):
            t = m.grid[y][x]
            m.grid[y][width-1-x] = t
    mid = width // 2
    gaps = set(random.sample(range(height), k=max(3, height//6)))
    for y in range(height):
        if y in gaps:
            continue
        m.grid[y][mid] = PLAIN
    for y in range(height):
        for x in range(min(3, width)):
            m.grid[y][x] = PLAIN
        for x in range(max(0, width-3), width):
            m.grid[y][x] = PLAIN
    return m
