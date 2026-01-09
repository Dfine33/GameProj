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
    
    # 1. Generate Noise for Mountains
    # Use Perlin-like noise smoothing
    noise = [[random.random() for _ in range(width)] for _ in range(height)]
    for _ in range(4): # Increased smoothing passes
        new_noise = [[0.0 for _ in range(width)] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                s = noise[y][x]
                c = 1
                if x > 0: s += noise[y][x-1]; c += 1
                if x+1 < width: s += noise[y][x+1]; c += 1
                if y > 0: s += noise[y-1][x]; c += 1
                if y+1 < height: s += noise[y+1][x]; c += 1
                new_noise[y][x] = s / c
        noise = new_noise

    # 2. Apply Terrain Thresholds (Top Half Only for Central Symmetry)
    # We process rows 0 to height//2 (exclusive) fully, 
    # and if height is odd, we'd handle the middle row carefully. 
    # For simplicity, assuming even height or just processing top half rows.
    half_h = height // 2
    for y in range(half_h):
        for x in range(width):
            v = noise[y][x]
            if v > 0.65:
                m.grid[y][x] = MOUNTAIN
            elif v > 0.55 and random.random() < 0.4:
                m.grid[y][x] = MOUNTAIN
            else:
                m.grid[y][x] = PLAIN

    # 3. Generate River (Separating Diagonals)
    # Bases are Top-Left and Bottom-Right.
    # River should flow roughly Top-Right to Bottom-Left.
    # We generate the Top-Right half of the river (from edge to center).
    # Start at random point on Top Edge (Right side) or Right Edge (Top side).
    
    river_start_options = []
    # Top edge, right half
    for x in range(width // 2 + 2, width - 2):
        river_start_options.append((x, 0))
    # Right edge, top half
    for y in range(height // 2 - 2):
        river_start_options.append((width - 1, y))
        
    if river_start_options:
        cx, cy = random.choice(river_start_options)
        m.grid[cy][cx] = RIVER
        
        # Target is center, but we clamp ny to half_h - 1.
        # So we should aim for (width // 2, half_h - 1)
        tx, ty = width // 2, half_h - 1
        
        # Simple walk
        loop_guard = 0
        while (cx != tx or cy != ty) and loop_guard < 1000:
            loop_guard += 1
            # Move towards center
            dx = 0
            dy = 0
            if cx < tx: dx = 1
            elif cx > tx: dx = -1
            
            if cy < ty: dy = 1
            elif cy > ty: dy = -1
            
            # Randomize slightly to meander, but bias towards center
            moves = []
            if dx != 0: moves.append((dx, 0))
            if dy != 0: moves.append((0, dy))
            
            if not moves: break
            
            mdx, mdy = random.choice(moves)
            # Occasional random deviation
            if random.random() < 0.3:
                mdx, mdy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                # Clamp direction to not go backwards too much? 
                # Simplest is just take the optimal move most of the time
                if dx != 0: mdx = dx; mdy = 0
                if dy != 0 and random.random() < 0.5: mdx = 0; mdy = dy
            
            nx, ny = cx + mdx, cy + mdy
            
            # Clamp to top half bounds
            nx = max(0, min(width - 1, nx))
            ny = max(0, min(half_h - 1, ny)) # Stay in top half (exclusive of center line for now)
            
            cx, cy = nx, ny
            m.grid[cy][cx] = RIVER
            
            # Widen randomly
            if random.random() < 0.2:
                for wx, wy in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
                    if m.in_bounds(wx, wy) and wy < half_h:
                        m.grid[wy][wx] = RIVER
        
        # Ensure center is RIVER to connect with the mirrored half
        # But we are mirroring 0..half_h-1.
        # The center point (if h is even) is effectively the join line.
        # If we want the river to cross the center, the 'end' of our river at (tx, half_h-1) 
        # will mirror to (width-1-tx, height-1-(half_h-1)) = (width-1-tx, half_h).
        # We need to ensure continuity. 
        # Let's force a few cells around center to be RIVER?
        # Or just PLAIN (Bridge at center)? 
        # A bridge at center is good for gameplay.
        pass

    # 4. Mirror Map (Central/Point Symmetry)
    # (x, y) -> (width-1-x, height-1-y)
    for y in range(half_h):
        for x in range(width):
            src = m.grid[y][x]
            m.grid[height - 1 - y][width - 1 - x] = src
            
    # If height is odd, handle middle row
    if height % 2 == 1:
        mid_y = height // 2
        for x in range(width // 2):
            src = m.grid[mid_y][x]
            m.grid[mid_y][width - 1 - x] = src
        # Center pixel
        if width % 2 == 1:
            # m.grid[mid_y][width // 2] is unique
            pass

    # 5. Clear Base Areas (Diagonal Corners)
    # Base A: Top-Left
    # Base B: Bottom-Right
    
    def clear_radius(cx, cy, r):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = cx + dx, cy + dy
                if m.in_bounds(nx, ny):
                    m.grid[ny][nx] = PLAIN

    base_margin = 3
    # Top-Left
    clear_radius(base_margin, base_margin, 3)
    # Bottom-Right
    clear_radius(width - 1 - base_margin, height - 1 - base_margin, 3)

    # 6. Ensure Bridges
    # Since we have a river separating diagonals, we need bridges.
    # The map is point symmetric. If we add a bridge at (x, y), we must add at (w-1-x, h-1-y).
    # Center Bridge
    cx, cy = width // 2, height // 2
    clear_radius(cx, cy, 1) # Central bridge
    
    # Random other bridges?
    # Let's add one more bridge in the top half river segment, and mirror it.
    # Scan for river cells in top half
    river_cells = []
    for y in range(half_h):
        for x in range(width):
            if m.grid[y][x] == RIVER:
                river_cells.append((x, y))
    
    if river_cells:
        # Pick a random spot for a flank bridge
        bx, by = random.choice(river_cells)
        clear_radius(bx, by, 1)
        # Mirror it
        clear_radius(width - 1 - bx, height - 1 - by, 1)

    return m
