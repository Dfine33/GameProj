import pygame
from renderer.base import Renderer
from core.map import PLAIN, MOUNTAIN, RIVER

class PygameRenderer(Renderer):
    def __init__(self, cell_size=24, fps=60):
        self.cell_size = cell_size
        self.fps = fps
        self.screen = None
        self.clock = None
        self.font = None
        self.running = True
        self.view_mode = 'ALL'
        self.ui_top = 88
        self.paused = False
        self.speed = 1.0
        self.ui_rects = {}
        self.colors = {
            'bg': (18, 18, 18),
            'grid': (32, 32, 32),
            PLAIN: (60, 120, 60),
            MOUNTAIN: (80, 80, 80),
            RIVER: (50, 90, 160),
            'A': (220, 70, 70),
            'B': (70, 160, 220),
            'text': (240, 240, 240),
            'hp_bar_bg': (100, 100, 100),
            'hp_bar_fg': (30, 200, 30)
        }

    def initialize(self, gamestate):
        pygame.init()
        w = gamestate.map.width * self.cell_size
        h = gamestate.map.height * self.cell_size + self.ui_top
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption('RTS 模拟')
        self.clock = pygame.time.Clock()
        self.font = self._load_font(18)
        self.title_font = self._load_font(28)

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

    def close(self):
        pygame.quit()

    def process_input(self):
        if self.screen is None:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.view_mode = 'A'
                elif event.key == pygame.K_2:
                    self.view_mode = 'B'
                elif event.key == pygame.K_3:
                    self.view_mode = 'ALL'

    def render(self, gamestate, tick):
        if self.screen is None:
            self.initialize(gamestate)
        self.screen.fill(self.colors['bg'])
        vis = None
        if self.view_mode in ('A','B'):
            vis = self.compute_visibility(gamestate, self.view_mode)
        self.render_map(gamestate, vis)
        self.render_bases(gamestate, vis)
        self.render_units(gamestate, vis)
        self.render_hud(gamestate, tick)
        pygame.display.flip()
        self.clock.tick(self.fps)
        return ''

    def render_map(self, gamestate, vis=None):
        for y in range(gamestate.map.height):
            for x in range(gamestate.map.width):
                t = gamestate.map.grid[y][x]
                color = self.colors.get(t, self.colors[PLAIN])
                rx = x * self.cell_size
                ry = y * self.cell_size + self.ui_top
                pygame.draw.rect(self.screen, color, pygame.Rect(rx, ry, self.cell_size, self.cell_size))
                if vis is not None and (x, y) not in vis:
                    s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    s.fill((0,0,0,160))
                    self.screen.blit(s, (rx, ry))

    def render_bases(self, gamestate, vis=None):
        bases = [gamestate.base_a, gamestate.base_b]
        for base in bases:
            if vis is not None and base.team != self.view_mode and base.pos() not in vis:
                kb = gamestate.known_enemy_base.get(self.view_mode)
                if kb == base.pos():
                    color = self.colors.get(base.team)
                    cx = base.x * self.cell_size + self.cell_size // 2
                    cy = base.y * self.cell_size + self.ui_top + self.cell_size // 2
                    r = self.cell_size // 2
                    pygame.draw.circle(self.screen, color, (cx, cy), r, 2)
                    continue
                else:
                    continue
            color = self.colors.get(base.team)
            cx = base.x * self.cell_size + self.cell_size // 2
            cy = base.y * self.cell_size + self.ui_top + self.cell_size // 2
            r = self.cell_size // 2
            pygame.draw.circle(self.screen, color, (cx, cy), r)
            bw = self.cell_size
            bh = 6
            bx = base.x * self.cell_size
            by = base.y * self.cell_size + self.ui_top - 8
            pygame.draw.rect(self.screen, self.colors['hp_bar_bg'], pygame.Rect(bx, by, bw, bh))
            ratio = max(0.0, min(1.0, base.hp / 500.0))
            pygame.draw.rect(self.screen, self.colors['hp_bar_fg'], pygame.Rect(bx, by, int(bw * ratio), bh))

    def render_units(self, gamestate, vis=None):
        for u in gamestate.units:
            if vis is not None and u.team != self.view_mode and (u.x, u.y) not in vis:
                continue
            color = self.colors.get(u.team)
            rx = u.x * self.cell_size
            ry = u.y * self.cell_size + self.ui_top
            if u.kind == 'Infantry':
                pygame.draw.rect(self.screen, color, pygame.Rect(rx + 6, ry + 6, self.cell_size - 12, self.cell_size - 12))
            elif u.kind == 'Archer':
                cx = rx + self.cell_size // 2
                cy = ry + self.cell_size // 2
                pygame.draw.circle(self.screen, color, (cx, cy), self.cell_size // 3)
            else:
                points = [(rx + self.cell_size // 2, ry + 4), (rx + 4, ry + self.cell_size - 4), (rx + self.cell_size - 4, ry + self.cell_size - 4)]
                pygame.draw.polygon(self.screen, color, points)

    def render_hud(self, gamestate, tick):
        feed_h = 24
        hud_h = 64
        top_panel = pygame.Surface((self.screen.get_width(), feed_h + hud_h))
        top_panel.set_alpha(220)
        top_panel.fill((10, 10, 12))
        self.screen.blit(top_panel, (0, 0))
        w = self.screen.get_width()
        a_ratio = max(0.0, min(1.0, gamestate.base_a.hp / 500.0))
        b_ratio = max(0.0, min(1.0, gamestate.base_b.hp / 500.0))
        bar_w = w // 2 - 60
        bar_h = 14
        ax = 20
        bx = w // 2 + 40
        y = feed_h + 18
        pygame.draw.rect(self.screen, self.colors['hp_bar_bg'], pygame.Rect(ax, y, bar_w, bar_h))
        pygame.draw.rect(self.screen, self.colors['A'], pygame.Rect(ax, y, int(bar_w * a_ratio), bar_h))
        pygame.draw.rect(self.screen, self.colors['hp_bar_bg'], pygame.Rect(bx, y, bar_w, bar_h))
        pygame.draw.rect(self.screen, self.colors['B'], pygame.Rect(bx, y, int(bar_w * b_ratio), bar_h))
        at = self.font.render(f"A HP {max(0, gamestate.base_a.hp)}", True, self.colors['text'])
        bt = self.font.render(f"B HP {max(0, gamestate.base_b.hp)}", True, self.colors['text'])
        self.screen.blit(at, (ax, y - 18))
        self.screen.blit(bt, (bx, y - 18))
        info = f"Tick {tick}  Units A {sum(1 for u in gamestate.units if u.team=='A')} / B {sum(1 for u in gamestate.units if u.team=='B')}  View {self.view_mode}"
        infs = self.font.render(info, True, self.colors['text'])
        self.screen.blit(infs, (20, feed_h + 44))
        for it in getattr(self, 'feed_items', []):
            surf = self.font.render(it.text, True, (240, 220, 80))
            self.screen.blit(surf, (int(it.x), int(it.y)))

        ctrl_y1 = feed_h + 12
        ctrl_y2 = feed_h + 38
        right = w - 20
        pause_rect = pygame.Rect(right - 26, ctrl_y1, 24, 24)
        sp_minus = pygame.Rect(right - 86, ctrl_y2, 24, 24)
        sp_plus = pygame.Rect(right - 26, ctrl_y2, 24, 24)
        self.ui_rects = {
            'pause': pause_rect,
            'speed_minus': sp_minus,
            'speed_plus': sp_plus,
        }
        pygame.draw.rect(self.screen, (60,60,70), pause_rect)
        pygame.draw.rect(self.screen, (120,120,140), pause_rect, 2)
        sym = '▶' if not self.paused else '⏸'
        symsurf = self.font.render(sym, True, self.colors['text'])
        self.screen.blit(symsurf, (pause_rect.x + 4, pause_rect.y + 2))

        lab1 = self.font.render('状态', True, self.colors['text'])
        self.screen.blit(lab1, (right - 130, ctrl_y1 + 4))
        stxt = self.font.render('运行' if not self.paused else '暂停', True, self.colors['text'])
        self.screen.blit(stxt, (right - 90, ctrl_y1 + 4))

        pygame.draw.rect(self.screen, (60,60,70), sp_minus)
        pygame.draw.rect(self.screen, (120,120,140), sp_minus, 2)
        msurf = self.font.render('-', True, self.colors['text'])
        self.screen.blit(msurf, (sp_minus.x + 6, sp_minus.y + 2))
        pygame.draw.rect(self.screen, (60,60,70), sp_plus)
        pygame.draw.rect(self.screen, (120,120,140), sp_plus, 2)
        psurf = self.font.render('+', True, self.colors['text'])
        self.screen.blit(psurf, (sp_plus.x + 6, sp_plus.y + 2))
        sval = self.font.render(f'{self.speed:.2f}x', True, self.colors['text'])
        self.screen.blit(sval, (right - 58, ctrl_y2 + 2))

    def compute_visibility(self, gamestate, side):
        def line_points(x0, y0, x1, y1):
            points = []
            dx = abs(x1 - x0)
            dy = -abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx + dy
            x, y = x0, y0
            while True:
                points.append((x, y))
                if x == x1 and y == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x += sx
                if e2 <= dx:
                    err += dx
                    y += sy
            return points
        vis = set()
        ents = [u for u in gamestate.units if u.team == side]
        base = gamestate.base_a if side == 'A' else gamestate.base_b
        ents.append(base)
        for e in ents:
            r = getattr(e, 'vision', 6)
            ex, ey = e.pos()
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    x = ex + dx
                    y = ey + dy
                    if not gamestate.map.in_bounds(x, y):
                        continue
                    if abs(dx) + abs(dy) > r:
                        continue
                    blocked = False
                    for px, py in line_points(ex, ey, x, y):
                        if (px, py) == (ex, ey):
                            continue
                        t = gamestate.map.grid[py][px]
                        if t == MOUNTAIN:
                            if (px, py) != (x, y):
                                blocked = True
                                break
                    if not blocked:
                        vis.add((x, y))
        return vis