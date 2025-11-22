import pygame
import math
from renderer.base import Renderer
from core.map import PLAIN, MOUNTAIN, RIVER
from utils.common import hex_line, hex_distance

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
        self.map_pad_x = int(self.cell_size)
        self.map_pad_top = int(self.cell_size)
        self.step_mode = False
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
        w = int(self.cell_size * math.sqrt(3) * (gamestate.map.width + 0.5)) + self.map_pad_x * 2
        h = int(self.cell_size * 1.5 * gamestate.map.height + self.ui_top + self.map_pad_top)
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
            gamestate.record_explored(self.view_mode, list(vis))
        self.render_map(gamestate, vis)
        self.render_bases(gamestate, vis)
        self.render_units(gamestate, vis)
        self.render_hud(gamestate, tick)
        pygame.display.flip()
        self.clock.tick(self.fps)
        return ''

    def render_map(self, gamestate, vis=None):
        size = self.cell_size
        side_exp = gamestate.explored.get(self.view_mode, set()) if self.view_mode in ('A','B') else None
        for y in range(gamestate.map.height):
            for x in range(gamestate.map.width):
                t = gamestate.map.grid[y][x]
                if self.view_mode in ('A','B'):
                    if (x, y) in side_exp:
                        color = self.colors.get(t, self.colors[PLAIN])
                    else:
                        color = self.colors.get(PLAIN)
                else:
                    color = self.colors.get(t, self.colors[PLAIN])
                cx = self.map_pad_x + size * math.sqrt(3) * (x + 0.5 * (y & 1))
                cy = self.ui_top + self.map_pad_top + size * 1.5 * y
                pts = []
                for i in range(6):
                    ang = math.pi/180 * (60 * i + 30)
                    px = cx + size * math.cos(ang)
                    py = cy + size * math.sin(ang)
                    pts.append((px, py))
                pygame.draw.polygon(self.screen, color, pts)
                if self.view_mode in ('A','B'):
                    if vis is not None and (x, y) in vis:
                        pass
                    elif (x, y) in side_exp:
                        self._poly_overlay(pts, (0, 0, 0, 80))
                    else:
                        self._poly_overlay(pts, (100, 100, 110, 160))
                self._stroke_dashed(pts, (60,60,70), 1)

    def render_bases(self, gamestate, vis=None):
        bases = [gamestate.base_a, gamestate.base_b]
        for base in bases:
            if vis is not None and base.team != self.view_mode and base.pos() not in vis:
                kb = gamestate.known_enemy_base.get(self.view_mode)
                if kb == base.pos():
                    color = self.colors.get(base.team)
                    cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (base.x + 0.5 * (base.y & 1))
                    cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * base.y
                    r = int(self.cell_size * 0.6)
                    pygame.draw.circle(self.screen, color, (int(cx), int(cy)), r, 2)
                    continue
                else:
                    continue
            color = self.colors.get(base.team)
            cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (base.x + 0.5 * (base.y & 1))
            cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * base.y
            r = int(self.cell_size * 0.6)
            pygame.draw.circle(self.screen, color, (int(cx), int(cy)), r)
            bw = int(self.cell_size * 1.6)
            bh = 6
            bx = int(cx - bw/2)
            by = int(cy - r - 10)
            pygame.draw.rect(self.screen, self.colors['hp_bar_bg'], pygame.Rect(bx, by, bw, bh))
            ratio = max(0.0, min(1.0, base.hp / 500.0))
            pygame.draw.rect(self.screen, self.colors['hp_bar_fg'], pygame.Rect(bx, by, int(bw * ratio), bh))

    def render_units(self, gamestate, vis=None):
        for u in gamestate.units:
            if vis is not None and u.team != self.view_mode and (u.x, u.y) not in vis:
                continue
            color = self.colors.get(u.team)
            cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (u.x + 0.5 * (u.y & 1))
            cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * u.y
            if u.kind == 'Infantry':
                pygame.draw.rect(self.screen, color, pygame.Rect(int(cx - 6), int(cy - 6), 12, 12))
            elif u.kind == 'Archer':
                pygame.draw.circle(self.screen, color, (int(cx), int(cy)), max(3, int(self.cell_size * 0.35)))
            else:
                points = [(int(cx), int(cy - 8)), (int(cx - 8), int(cy + 8)), (int(cx + 8), int(cy + 8))]
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
        step_toggle = pygame.Rect(right - 56, ctrl_y1, 24, 24)
        sp_minus = pygame.Rect(right - 86, ctrl_y2, 24, 24)
        step_once = pygame.Rect(right - 56, ctrl_y2, 24, 24)
        sp_plus = pygame.Rect(right - 26, ctrl_y2, 24, 24)
        self.ui_rects = {
            'pause': pause_rect,
            'step_mode': step_toggle,
            'step_once': step_once,
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
        pygame.draw.rect(self.screen, (60,60,70), step_toggle)
        pygame.draw.rect(self.screen, (120,120,140), step_toggle, 2)
        mtxt = self.font.render('S', True, self.colors['text'])
        self.screen.blit(mtxt, (step_toggle.x + 6, step_toggle.y + 2))
        labm = self.font.render('模式', True, self.colors['text'])
        self.screen.blit(labm, (right - 190, ctrl_y1 + 4))
        mval = self.font.render('逐步' if self.step_mode else '连续', True, self.colors['text'])
        self.screen.blit(mval, (right - 150, ctrl_y1 + 4))

        pygame.draw.rect(self.screen, (60,60,70), sp_minus)
        pygame.draw.rect(self.screen, (120,120,140), sp_minus, 2)
        msurf = self.font.render('-', True, self.colors['text'])
        self.screen.blit(msurf, (sp_minus.x + 6, sp_minus.y + 2))
        pygame.draw.rect(self.screen, (60,60,70), step_once)
        pygame.draw.rect(self.screen, (120,120,140), step_once, 2)
        osurf = self.font.render('⏭', True, self.colors['text'])
        self.screen.blit(osurf, (step_once.x + 2, step_once.y + 2))
        pygame.draw.rect(self.screen, (60,60,70), sp_plus)
        pygame.draw.rect(self.screen, (120,120,140), sp_plus, 2)
        psurf = self.font.render('+', True, self.colors['text'])
        self.screen.blit(psurf, (sp_plus.x + 6, sp_plus.y + 2))
        sval = self.font.render(f'{self.speed:.2f}x', True, self.colors['text'])
        self.screen.blit(sval, (right - 58, ctrl_y2 + 2))

    def compute_visibility(self, gamestate, side):
        vis = set()
        ents = [u for u in gamestate.units if u.team == side]
        base = gamestate.base_a if side == 'A' else gamestate.base_b
        ents.append(base)
        for e in ents:
            r = getattr(e, 'vision', 6)
            ex, ey = e.pos()
            y0 = max(0, ey - r)
            y1 = min(gamestate.map.height - 1, ey + r)
            x0 = max(0, ex - r)
            x1 = min(gamestate.map.width - 1, ex + r)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if hex_distance((ex, ey), (x, y)) > r:
                        continue
                    blocked = False
                    for px, py in hex_line((ex, ey), (x, y)):
                        if (px, py) == (ex, ey):
                            continue
                        if not gamestate.map.in_bounds(px, py):
                            blocked = True
                            break
                        t = gamestate.map.grid[py][px]
                        if t == MOUNTAIN and (px, py) != (x, y):
                            blocked = True
                            break
                    if not blocked:
                        vis.add((x, y))
        return vis

    def _poly_overlay(self, pts, color):
        minx = min(p[0] for p in pts)
        maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts)
        maxy = max(p[1] for p in pts)
        w = int(maxx - minx) + 2
        h = int(maxy - miny) + 2
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        adj = [(p[0] - minx + 1, p[1] - miny + 1) for p in pts]
        pygame.draw.polygon(overlay, color, adj)
        self.screen.blit(overlay, (int(minx), int(miny)))
    def _stroke_dashed(self, pts, color, width):
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