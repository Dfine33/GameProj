import math
import os
import pygame
from core.map import PLAIN, MOUNTAIN, RIVER
from utils.common import hex_neighbors, hex_distance, hex_line

class VisionPathTester:
    def __init__(self, width=60, height=30, cell_size=24, ui_top=64, pad_x=24, pad_top=24):
        self.width = width
        self.height = height
        self.grid = [[PLAIN for _ in range(width)] for _ in range(height)]
        self.cell_size = cell_size
        self.ui_top = ui_top
        self.pad_x = pad_x
        self.pad_top = pad_top
        self.running = True
        self.current = PLAIN
        self.font = None
        self.title_font = None
        self.colors = {
            PLAIN: (60, 120, 60),
            MOUNTAIN: (80, 80, 80),
            RIVER: (50, 90, 160),
            'text': (240, 240, 240),
            'grid': (60,60,70),
            'A': (220, 70, 70),
            'B': (70, 160, 220),
            'vis': (230, 210, 80, 90),
            'path': (240,240,120),
        }
        self.mode = 'terrain'
        self.unit_pos = {'A': None, 'B': None}
        self.target = None
        self.vision_on = True
        self.vision_side = 'A'
        self.vision_range = 6
        self.vis_cells = set()
        self.path = []

    def initialize(self):
        pygame.init()
        w = int(self.cell_size * math.sqrt(3) * (self.width + 0.5)) + self.pad_x * 2
        h = int(self.cell_size * 1.5 * self.height + self.ui_top + self.pad_top)
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption('视野与路径调试器')
        self.clock = pygame.time.Clock()
        self.font = self._load_font(18)
        self.title_font = self._load_font(26)

    def _load_font(self, size):
        candidates = ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'Segoe UI Symbol', 'Noto Sans CJK SC', 'Source Han Sans SC', 'Consolas']
        for name in candidates:
            try:
                path = pygame.font.match_font(name)
                if path:
                    return pygame.font.Font(path, size)
            except Exception:
                continue
        return pygame.font.SysFont(None, size)

    def hex_center(self, x, y):
        cx = self.pad_x + self.cell_size * math.sqrt(3) * (x + 0.5 * (y & 1))
        cy = self.ui_top + self.pad_top + self.cell_size * 1.5 * y
        return cx, cy

    def pixel_to_hex(self, px, py):
        ry = (py - (self.ui_top + self.pad_top)) / (1.5 * self.cell_size)
        y = int(round(ry))
        if y < 0 or y >= self.height:
            return None
        offset = 0.5 * (y & 1) * self.cell_size * math.sqrt(3)
        rx = (px - self.pad_x - offset) / (self.cell_size * math.sqrt(3))
        x = int(round(rx))
        if x < 0 or x >= self.width:
            return None
        return x, y

    def draw_hex(self, cx, cy, color):
        pts = []
        for i in range(6):
            ang = math.pi/180 * (60 * i + 30)
            px = cx + self.cell_size * math.cos(ang)
            py = cy + self.cell_size * math.sin(ang)
            pts.append((px, py))
        pygame.draw.polygon(self.screen, color, pts)
        self.stroke_dashed(pts, (60,60,70), 1)
        return pts

    def stroke_dashed(self, pts, color, width):
        dash = 4
        gap = 2
        for i in range(len(pts)):
            x1, y1 = pts[i]
            x2, y2 = pts[(i+1) % len(pts)]
            dx = x2 - x1
            dy = y2 - y1
            dist = math.hypot(dx, dy)
            if dist <= 0:
                continue
            vx = dx / dist
            vy = dy / dist
            pos = 0.0
            while pos + dash <= dist:
                sx = x1 + vx * pos
                sy = y1 + vy * pos
                ex = x1 + vx * (pos + dash)
                ey = y1 + vy * (pos + dash)
                pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), width)
                pos += dash + gap

    def compute_visibility(self):
        self.vis_cells = set()
        side = self.vision_side
        upos = self.unit_pos.get(side)
        if not upos:
            return
        ux, uy = upos
        rng = self.vision_range
        for y in range(self.height):
            for x in range(self.width):
                if hex_distance((ux, uy), (x, y)) <= rng:
                    line = hex_line((ux, uy), (x, y))
                    blocked = False
                    for lx, ly in line[1:]:
                        if lx < 0 or ly < 0 or lx >= self.width or ly >= self.height:
                            blocked = True
                            break
                        if self.grid[ly][lx] == MOUNTAIN:
                            blocked = True
                            break
                    if not blocked:
                        self.vis_cells.add((x, y))

    def bfs_path(self, start, goal):
        from collections import deque
        if not start or not goal:
            return []
        sx, sy = start
        tx, ty = goal
        dq = deque()
        dq.append((sx, sy))
        prev = {}
        seen = {(sx, sy)}
        while dq:
            x, y = dq.popleft()
            if (x, y) == (tx, ty):
                break
            for nx, ny in hex_neighbors(x, y):
                if nx < 0 or ny < 0 or nx >= self.width or ny >= self.height:
                    continue
                if (nx, ny) in seen:
                    continue
                if self.grid[ny][nx] == PLAIN:
                    seen.add((nx, ny))
                    prev[(nx, ny)] = (x, y)
                    dq.append((nx, ny))
        path = []
        cur = (tx, ty)
        if cur not in prev and cur != (sx, sy):
            return []
        while cur != (sx, sy):
            path.append(cur)
            cur = prev.get(cur, (sx, sy))
        path.append((sx, sy))
        path.reverse()
        return path

    def render(self):
        self.screen.fill((18,18,18))
        top = pygame.Surface((self.screen.get_width(), self.ui_top))
        top.set_alpha(220)
        top.fill((10,10,12))
        self.screen.blit(top, (0,0))
        title = self.title_font.render('视野与路径调试器', True, self.colors['text'])
        self.screen.blit(title, (16, 16))
        info = f'模式 {self.mode}  侧 {self.vision_side}  视野 {self.vision_range}'
        ptxt = self.font.render(info, True, self.colors['text'])
        self.screen.blit(ptxt, (16, 44))
        for y in range(self.height):
            for x in range(self.width):
                cx, cy = self.hex_center(x, y)
                pts = self.draw_hex(cx, cy, self.colors[self.grid[y][x]])
                if self.vision_on and (x, y) in self.vis_cells:
                    s = pygame.Surface((self.cell_size*2, self.cell_size*2), pygame.SRCALPHA)
                    pygame.draw.polygon(s, self.colors['vis'], [(px-cx+self.cell_size, py-cy+self.cell_size) for px, py in pts])
                    self.screen.blit(s, (cx-self.cell_size, cy-self.cell_size))
        for side, pos in self.unit_pos.items():
            if pos:
                cx, cy = self.hex_center(pos[0], pos[1])
                pygame.draw.circle(self.screen, self.colors[side], (int(cx), int(cy)), int(self.cell_size*0.6), 2)
        if self.target:
            cx, cy = self.hex_center(self.target[0], self.target[1])
            pygame.draw.circle(self.screen, (220, 200, 80), (int(cx), int(cy)), int(self.cell_size*0.4), 2)
        if len(self.path) >= 2:
            ppts = []
            for (x, y) in self.path:
                cx, cy = self.hex_center(x, y)
                ppts.append((cx, cy))
            for i in range(len(ppts)-1):
                pygame.draw.line(self.screen, self.colors['path'], ppts[i], ppts[i+1], 2)
        pygame.display.flip()

    def run(self):
        self.initialize()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    uni = (event.unicode or '').lower()
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_1 or uni == '1':
                        self.current = PLAIN
                        self.mode = 'terrain'
                    elif event.key == pygame.K_2 or uni == '2':
                        self.current = MOUNTAIN
                        self.mode = 'terrain'
                    elif event.key == pygame.K_3 or uni == '3':
                        self.current = RIVER
                        self.mode = 'terrain'
                    elif event.key == pygame.K_a or uni == 'a':
                        self.mode = 'unitA'
                    elif event.key == pygame.K_b or uni == 'b':
                        self.mode = 'unitB'
                    elif event.key == pygame.K_t or uni == 't':
                        self.mode = 'target'
                    elif event.key == pygame.K_v or uni == 'v':
                        self.vision_on = not self.vision_on
                    elif event.key == pygame.K_r or uni == 'r':
                        self.vision_side = 'A' if self.vision_side == 'B' else 'B'
                        self.compute_visibility()
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        self.vision_range = min(12, self.vision_range + 1)
                        self.compute_visibility()
                    elif event.key == pygame.K_MINUS:
                        self.vision_range = max(1, self.vision_range - 1)
                        self.compute_visibility()
                    elif event.key == pygame.K_p or uni == 'p':
                        upos = self.unit_pos.get(self.vision_side)
                        if upos and self.target:
                            self.path = self.bfs_path(upos, self.target)
                    elif event.key == pygame.K_c or uni == 'c':
                        self.path = []
                    elif event.key == pygame.K_s or uni == 's':
                        os.makedirs('maps', exist_ok=True)
                        path = os.path.join('maps', 'debug_map.json')
                        import json
                        data = {'map': {'width': self.width, 'height': self.height, 'grid': self.grid}, 'units': [{'team': k, 'x': v[0], 'y': v[1]} for k, v in self.unit_pos.items() if v], 'target': self.target}
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1,3):
                    pos = self.pixel_to_hex(*event.pos)
                    if pos:
                        x, y = pos
                        if self.mode == 'terrain':
                            self.grid[y][x] = self.current
                            self.compute_visibility()
                        elif self.mode == 'unitA':
                            self.unit_pos['A'] = (x, y)
                            self.compute_visibility()
                        elif self.mode == 'unitB':
                            self.unit_pos['B'] = (x, y)
                            self.compute_visibility()
                        elif self.mode == 'target':
                            self.target = (x, y)
                            upos = self.unit_pos.get(self.vision_side)
                            if upos:
                                self.path = self.bfs_path(upos, self.target)
            self.render()
            self.clock.tick(60)
        pygame.quit()

def main():
    app = VisionPathTester()
    app.run()

if __name__ == '__main__':
    main()
