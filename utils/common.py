def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def adjacent_positions(x, y):
    return [(x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1)]