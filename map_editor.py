import os
import json
import math
import pygame
from core.map import PLAIN, MOUNTAIN, RIVER

class MapEditor:
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
        }
        self.mode = 'terrain'
        self.base_pos = {'A': None, 'B': None}

    def initialize(self):
        pygame.init()
        w = int(self.cell_size * math.sqrt(3) * (self.width + 0.5)) + self.pad_x * 2
        h = int(self.cell_size * 1.5 * self.height + self.ui_top + self.pad_top)
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption('地图编辑器')
        self.clock = pygame.time.Clock()
        self.font = self._load_font(18)
        self.title_font = self._load_font(26)
        self.naming = False
        self.name_input = ''

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

    def render(self):
        self.screen.fill((18,18,18))
        top = pygame.Surface((self.screen.get_width(), self.ui_top))
        top.set_alpha(220)
        top.fill((10,10,12))
        self.screen.blit(top, (0,0))
        title = self.title_font.render('地图编辑器', True, self.colors['text'])
        self.screen.blit(title, (16, 16))
        bp_a = self.base_pos['A']
        bp_b = self.base_pos['B']
        bp_txt = f"A基地 {bp_a if bp_a else '未放置'}  B基地 {bp_b if bp_b else '未放置'}"
        palette = f'模式 {self.mode} | 当前地形 {self.current}  切换: 1 平原 / 2 山 / 3 河  保存: S  退出: Esc  放置基地: A/B  返回地形: T'
        ptxt = self.font.render(palette, True, self.colors['text'])
        self.screen.blit(ptxt, (16, 44))
        p2 = self.font.render(bp_txt, True, self.colors['text'])
        self.screen.blit(p2, (16, 64))
        for y in range(self.height):
            for x in range(self.width):
                cx, cy = self.hex_center(x, y)
                self.draw_hex(cx, cy, self.colors[self.grid[y][x]])
        for side, pos in self.base_pos.items():
            if pos:
                cx, cy = self.hex_center(pos[0], pos[1])
                pygame.draw.circle(self.screen, self.colors[side], (int(cx), int(cy)), int(self.cell_size*0.6), 2)
        if self.naming:
            w, h = self.screen.get_size()
            box_w = 520
            box_h = 140
            panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            panel.fill((20, 20, 24, 240))
            bx = (w - box_w) // 2
            by = (h - box_h) // 2
            self.screen.blit(panel, (bx, by))
            t1 = self.title_font.render('输入地图名称', True, self.colors['text'])
            self.screen.blit(t1, (bx + 24, by + 20))
            t2 = self.font.render(self.name_input or '（仅支持字母数字下划线与短横线）', True, self.colors['text'])
            self.screen.blit(t2, (bx + 24, by + 70))
            hint = self.font.render('Enter 确认 / Esc 取消', True, self.colors['text'])
            self.screen.blit(hint, (bx + 24, by + 100))
        pygame.display.flip()

    def save(self, name=None):
        bases = []
        if self.base_pos['A']:
            bases.append({'team':'A','x':self.base_pos['A'][0],'y':self.base_pos['A'][1],'hp':500})
        if self.base_pos['B']:
            bases.append({'team':'B','x':self.base_pos['B'][0],'y':self.base_pos['B'][1],'hp':500})
        data = {
            'tick': 0,
            'map': {'width': self.width, 'height': self.height, 'grid': self.grid},
            'grid_type': 'hex',
            'layout': 'odd-r',
            'bases': bases,
            'units': [],
            'known_enemy_base': {'A': None, 'B': None},
            'explored': {'A': [], 'B': []},
        }
        os.makedirs('maps', exist_ok=True)
        if name:
            safe = ''.join(ch for ch in name if (ch.isalnum() or ch in ('_', '-')))
            if not safe:
                safe = f'map_{self.width}x{self.height}'
            filename = f'{safe}.json'
        else:
            filename = f'map_{self.width}x{self.height}_{pygame.time.get_ticks()}.json'
        path = os.path.join('maps', filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def run(self):
        self.initialize()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    uni = (event.unicode or '').lower()
                    if self.naming:
                        if event.key == pygame.K_ESCAPE:
                            self.naming = False
                            self.name_input = ''
                        elif event.key == pygame.K_RETURN:
                            self.save(self.name_input)
                            self.naming = False
                            self.name_input = ''
                        elif event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        else:
                            if uni and (uni.isalnum() or uni in ('_', '-')):
                                self.name_input += uni
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_1 or uni == '1':
                            self.current = PLAIN
                        elif event.key == pygame.K_2 or uni == '2':
                            self.current = MOUNTAIN
                        elif event.key == pygame.K_3 or uni == '3':
                            self.current = RIVER
                        elif event.key == pygame.K_s or uni == 's':
                            self.naming = True
                        elif event.key == pygame.K_a or uni == 'a':
                            self.mode = 'baseA'
                        elif event.key == pygame.K_b or uni == 'b':
                            self.mode = 'baseB'
                        elif event.key == pygame.K_t or uni == 't':
                            self.mode = 'terrain'
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1,3):
                    pos = self.pixel_to_hex(*event.pos)
                    if pos:
                        x, y = pos
                        if self.mode == 'terrain':
                            self.grid[y][x] = self.current
                            if event.button == 3:
                                mx = self.width - 1 - x
                                self.grid[y][mx] = self.current
                        elif self.mode == 'baseA':
                            self.base_pos['A'] = (x, y)
                            if event.button == 3:
                                mx = self.width - 1 - x
                                self.base_pos['B'] = (mx, y)
                        elif self.mode == 'baseB':
                            self.base_pos['B'] = (x, y)
                            if event.button == 3:
                                mx = self.width - 1 - x
                                self.base_pos['A'] = (mx, y)
            self.render()
            self.clock.tick(60)
        pygame.quit()

def main():
    editor = MapEditor(width=60, height=30)
    editor.run()

if __name__ == '__main__':
    main()
