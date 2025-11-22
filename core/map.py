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
    for _ in range(int(width*height*0.08)):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        m.grid[y][x] = MOUNTAIN
    if random.random() < 0.5:
        y = random.randint(5, height-6)
        gap = random.sample(range(width), k=max(3, width//10))
        for x in range(width):
            if x in gap:
                continue
            m.grid[y][x] = RIVER
    else:
        x = random.randint(5, width-6)
        gap = random.sample(range(height), k=max(3, height//6))
        for y in range(height):
            if y in gap:
                continue
            m.grid[y][x] = RIVER
    return m