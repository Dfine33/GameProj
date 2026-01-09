import pygame
import math
from renderer.base import Renderer
from core.map import PLAIN, MOUNTAIN, RIVER
from utils.common import hex_line, hex_distance, hex_neighbors

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
        self.preview_recruits = []
        self.preview_actions = {}
        self.preview_paths = {}
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
        self.clock = pygame.time.Clock()
        self.font = self._load_font(18)
        self.title_font = self._load_font(28)
        
        w = int(self.cell_size * math.sqrt(3) * (gamestate.map.width + 0.5)) + self.map_pad_x * 2
        h = int(self.cell_size * 1.5 * gamestate.map.height + self.ui_top + self.map_pad_top)
        
        # Enforce minimum size and use handle_resize for setup
        w = max(800, w)
        h = max(600, h)
        self.handle_resize(w, h, gamestate)
        
        pygame.display.set_caption('RTS 模拟')

    def handle_resize(self, w, h, gamestate):
        MIN_W, MIN_H = 800, 600
        if w < MIN_W: w = MIN_W
        if h < MIN_H: h = MIN_H
        
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        
        # Calculate available space for map
        map_w_avail = w - 40 # padding
        map_h_avail = h - self.ui_top - 40 # padding
        
        if map_w_avail < 100: map_w_avail = 100
        if map_h_avail < 100: map_h_avail = 100

        map_hex_w = math.sqrt(3) * (gamestate.map.width + 0.5)
        map_hex_h = 1.5 * gamestate.map.height + 0.5
        
        cell_w = map_w_avail / map_hex_w
        cell_h = map_h_avail / map_hex_h
        
        new_cell_size = min(cell_w, cell_h)
        self.cell_size = max(4, new_cell_size) # Minimum cell size
        
        # Recalculate padding to center
        actual_map_w = self.cell_size * map_hex_w
        actual_map_h = self.cell_size * map_hex_h
        
        self.map_pad_x = max(0, int((w - actual_map_w) / 2))
        
        avail_h_for_map = h - self.ui_top
        self.map_pad_top = max(0, int((avail_h_for_map - actual_map_h) / 2))

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
        self.render_overlays(gamestate)
        self.render_panel(gamestate)
        self.render_hud(gamestate, tick)
        pygame.display.flip()
        self.clock.tick(self.fps)
        return ''

    def pixel_to_hex(self, px, py):
        ry = (py - (self.ui_top + self.map_pad_top)) / (1.5 * self.cell_size)
        y = int(round(ry))
        if y < 0 or y >= getattr(self, 'last_h', 0):
            pass
        offset = 0.5 * (y & 1) * self.cell_size * math.sqrt(3)
        rx = (px - self.map_pad_x - offset) / (self.cell_size * math.sqrt(3))
        x = int(round(rx))
        return (x, y)

    def _draw_ghost_unit(self, kind, team, x, y):
        cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (x + 0.5 * (y & 1))
        cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * y
        color = self.colors.get(team, (200,200,200))
        overlay = pygame.Surface((int(self.cell_size*2), int(self.cell_size*2)), pygame.SRCALPHA)
        ox = int(cx - self.cell_size)
        oy = int(cy - self.cell_size)
        
        # Proportional sizing
        unit_size = max(2, int(self.cell_size * 0.5))
        offset = self.cell_size - unit_size
        
        if kind == 'Infantry':
            pygame.draw.rect(overlay, (*color, 140), pygame.Rect(offset, offset, unit_size*2, unit_size*2))
        elif kind == 'Archer':
            pygame.draw.circle(overlay, (*color, 140), (self.cell_size, self.cell_size), unit_size)
        else:
            pts = [(self.cell_size, self.cell_size - unit_size), (self.cell_size - unit_size, self.cell_size + unit_size), (self.cell_size + unit_size, self.cell_size + unit_size)]
            pygame.draw.polygon(overlay, (*color, 140), pts)
        self.screen.blit(overlay, (ox, oy))

    def _draw_arrow(self, sx, sy, tx, ty, color):
        pygame.draw.line(self.screen, color, (sx, sy), (tx, ty), 2)
        ang = math.atan2(ty - sy, tx - sx)
        l = 10
        hx1 = tx - l * math.cos(ang - math.pi/6)
        hy1 = ty - l * math.sin(ang - math.pi/6)
        hx2 = tx - l * math.cos(ang + math.pi/6)
        hy2 = ty - l * math.sin(ang + math.pi/6)
        pygame.draw.polygon(self.screen, color, [(tx, ty), (hx1, hy1), (hx2, hy2)])

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
                # 选中高亮描边
                if getattr(self, 'ui_highlights', None) and (x, y) in self.ui_highlights:
                    pygame.draw.polygon(self.screen, (240,220,80), pts, 3)
        self.last_w = gamestate.map.width
        self.last_h = gamestate.map.height

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
            
            # Base HP bar
            bw = max(4, int(self.cell_size * 1.6))
            bh = max(2, int(self.cell_size * 0.2))
            bx = int(cx - bw/2)
            by = int(cy - r - bh - 2)
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
            
            unit_size = max(2, int(self.cell_size * 0.5))
            
            if u.kind == 'Infantry':
                pygame.draw.rect(self.screen, color, pygame.Rect(int(cx - unit_size), int(cy - unit_size), unit_size*2, unit_size*2))
            elif u.kind == 'Archer':
                pygame.draw.circle(self.screen, color, (int(cx), int(cy)), unit_size)
            else:
                points = [(int(cx), int(cy - unit_size)), (int(cx - unit_size), int(cy + unit_size)), (int(cx + unit_size), int(cy + unit_size))]
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
        bar_w = max(50, w // 2 - 240)
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
        info = f"回合 {tick}  Units A {sum(1 for u in gamestate.units if u.team=='A')} / B {sum(1 for u in gamestate.units if u.team=='B')}  View {self.view_mode}"
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
        end_turn = pygame.Rect(right - 146, ctrl_y2, 50, 24)
        self.ui_rects = {
            'pause': pause_rect,
            'step_mode': step_toggle,
            'step_once': step_once,
            'speed_minus': sp_minus,
            'speed_plus': sp_plus,
            'end_turn': end_turn,
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
        
        # Determine "End Turn" button appearance based on waiting state
        is_waiting = getattr(self, 'is_waiting_pvp', False)
        
        et_color = (60,60,70)
        et_text = '结束'
        if is_waiting:
             et_color = (80, 40, 40)
             et_text = '取消'
        
        pygame.draw.rect(self.screen, et_color, end_turn)
        pygame.draw.rect(self.screen, (120,120,140), end_turn, 2)
        etxt = self.font.render(et_text, True, self.colors['text'])
        self.screen.blit(etxt, (end_turn.x + 8, end_turn.y + 2))
        
        if is_waiting:
            # Draw waiting overlay
            wait_text = self.title_font.render("等待对手...", True, (255, 255, 255))
            wrect = wait_text.get_rect(center=(w//2, 80))
            self.screen.blit(wait_text, wrect)

        # Draw PVP Error Overlay
        err_msg = getattr(self, 'pvp_error', None)
        if err_msg:
            s = pygame.Surface((w, 60))
            s.set_alpha(200)
            s.fill((100, 0, 0))
            self.screen.blit(s, (0, self.screen.get_height()//2 - 30))
            etext = self.title_font.render(err_msg, True, (255, 255, 255))
            erect = etext.get_rect(center=(w//2, self.screen.get_height()//2))
            self.screen.blit(etext, erect)

    def render_overlays(self, gamestate):
        hl = getattr(self, 'ui_highlights', set())
        color = (230, 210, 80, 100)
        for (x, y) in hl:
            size = self.cell_size
            cx = self.map_pad_x + size * math.sqrt(3) * (x + 0.5 * (y & 1))
            cy = self.ui_top + self.map_pad_top + size * 1.5 * y
            pts = []
            for i in range(6):
                ang = math.pi/180 * (60 * i + 30)
                px = cx + size * math.cos(ang)
                py = cy + size * math.sin(ang)
                pts.append((px, py))
            self._poly_overlay(pts, color)
        # 预览：招募与单位行动
        for rec in getattr(self, 'preview_recruits', []):
            self._draw_ghost_unit(rec.get('kind','Infantry'), rec.get('team','A'), rec['pos'][0], rec['pos'][1])
        for u, act in getattr(self, 'preview_actions', {}).items():
            if act.kind == 'move_towards':
                tx, ty = act.target
                self._draw_ghost_unit(u.kind, u.team, tx, ty)
                path = self.preview_paths.get(u, [])
                if len(path) >= 2:
                    ppts = []
                    for (x, y) in path:
                        cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (x + 0.5 * (y & 1))
                        cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * y
                        ppts.append((cx, cy))
                    for i in range(len(ppts)-1):
                        pygame.draw.line(self.screen, (240,240,120), ppts[i], ppts[i+1], 2)
            elif act.kind == 'move_path':
                path = self.preview_paths.get(u, [])
                if path:
                    tx, ty = path[-1]
                    self._draw_ghost_unit(u.kind, u.team, tx, ty)
                    if len(path) >= 2:
                        ppts = []
                        for (x, y) in path:
                            cx = self.map_pad_x + self.cell_size * math.sqrt(3) * (x + 0.5 * (y & 1))
                            cy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * y
                            ppts.append((cx, cy))
                        for i in range(len(ppts)-1):
                            pygame.draw.line(self.screen, (240,240,120), ppts[i], ppts[i+1], 2)
            elif act.kind == 'attack':
                tgt = act.target
                x, y = tgt.pos()
                size = self.cell_size
                cx = self.map_pad_x + size * math.sqrt(3) * (x + 0.5 * (y & 1))
                cy = self.ui_top + self.map_pad_top + size * 1.5 * y
                pts = []
                for i in range(6):
                    ang = math.pi/180 * (60 * i + 30)
                    px = cx + size * math.cos(ang)
                    py = cy + size * math.sin(ang)
                    pts.append((px, py))
                self._poly_overlay(pts, (220,70,70,120))
                pygame.draw.polygon(self.screen, (220,70,70), pts, 3)
                # 攻击箭头预览
                sx = self.map_pad_x + self.cell_size * math.sqrt(3) * (u.x + 0.5 * (u.y & 1))
                sy = self.ui_top + self.map_pad_top + self.cell_size * 1.5 * u.y
                self._draw_arrow(sx, sy, cx, cy, (220,70,70))

    def render_panel(self, gamestate):
        panel = getattr(self, 'panel', None)
        self.panel_rects = {}
        if not panel:
            return
        w = 280
        h = 200
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((16,16,20,220))
        px = 16
        py = self.ui_top + 8
        self.screen.blit(surf, (px, py))
        title = panel.get('title', '')
        t = self.title_font.render(title, True, self.colors['text'])
        self.screen.blit(t, (px + 10, py + 8))
        if panel.get('type') == 'base':
            pts = panel.get('points', 0)
            tt = self.font.render(f'点数 {pts}', True, (220,220,220))
            self.screen.blit(tt, (px + 10, py + 44))
            items = panel.get('items', [])
            selected_item = panel.get('selected_item')
            y = py + 70
            for item in items:
                r = pygame.Rect(px + 10, y, w - 20, 28)
                fill = (90,90,110) if item['name'] == selected_item else (60,60,70)
                brd = (240,220,80) if item['name'] == selected_item else (120,120,140)
                pygame.draw.rect(self.screen, fill, r)
                pygame.draw.rect(self.screen, brd, r, 3 if item['name'] == selected_item else 2)
                label = f"{item['name']}  消耗{item['cost']}  ATK{item['atk']} HP{item['hp']} SPD{item['spd']}"
                ts = self.font.render(label, True, self.colors['text'])
                self.screen.blit(ts, (r.x + 6, r.y + 4))
                self.panel_rects[item['name']] = r
                y += 34
            undo = pygame.Rect(px + w - 90, py + h - 36, 74, 24)
            pygame.draw.rect(self.screen, (60,60,70), undo)
            pygame.draw.rect(self.screen, (200,160,60), undo, 2)
            uts = self.font.render('撤回', True, self.colors['text'])
            self.screen.blit(uts, (undo.x + 18, undo.y + 2))
            self.panel_rects['undo'] = undo
        elif panel.get('type') == 'unit':
            unit = panel.get('unit')
            hp_ratio = max(0.0, min(1.0, unit.hp / max(1, panel.get('max_hp', unit.hp))))
            bar = pygame.Rect(px + 10, py + 44, w - 20, 14)
            pygame.draw.rect(self.screen, (100,100,100), bar)
            pygame.draw.rect(self.screen, (30,200,30), pygame.Rect(bar.x, bar.y, int(bar.width * hp_ratio), bar.height))
            ts = self.font.render(f'移动点 {unit.spd}', True, self.colors['text'])
            self.screen.blit(ts, (px + 10, py + 64))
            # 操作模式按钮
            mv = pygame.Rect(px + 10, py + 88, 60, 24)
            at = pygame.Rect(px + 80, py + 88, 60, 24)
            sel_mode = panel.get('selected_mode')
            pygame.draw.rect(self.screen, (90,90,110) if sel_mode=='move' else (60,60,70), mv)
            pygame.draw.rect(self.screen, (240,220,80) if sel_mode=='move' else (120,120,140), mv, 3 if sel_mode=='move' else 2)
            pygame.draw.rect(self.screen, (90,90,110) if sel_mode=='attack' else (60,60,70), at)
            pygame.draw.rect(self.screen, (240,220,80) if sel_mode=='attack' else (120,120,140), at, 3 if sel_mode=='attack' else 2)
            mvts = self.font.render('移动', True, self.colors['text'])
            atts = self.font.render('攻击', True, self.colors['text'])
            self.screen.blit(mvts, (mv.x + 12, mv.y + 2))
            self.screen.blit(atts, (at.x + 12, at.y + 2))
            self.panel_rects['unit_move'] = mv
            self.panel_rects['unit_attack'] = at
            # 目标列表
            y = py + 120
            for i, tgt in enumerate(panel.get('targets', [])):
                rr = pygame.Rect(px + 10, y, w - 20, 24)
                pygame.draw.rect(self.screen, (60,60,70), rr)
                pygame.draw.rect(self.screen, (120,120,140), rr, 2)
                name = '基地' if not hasattr(tgt, 'kind') else f'{tgt.team}-{tgt.kind}'
                est = self.font.render(f'目标: {name}', True, self.colors['text'])
                self.screen.blit(est, (rr.x + 6, rr.y + 2))
                self.panel_rects[f'target_{i}'] = rr
                y += 28
            undo = pygame.Rect(px + w - 90, py + h - 36, 74, 24)
            pygame.draw.rect(self.screen, (60,60,70), undo)
            pygame.draw.rect(self.screen, (120,120,140), undo, 2)
            uts = self.font.render('撤回', True, self.colors['text'])
            self.screen.blit(uts, (undo.x + 18, undo.y + 2))
            self.panel_rects['undo'] = undo

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
