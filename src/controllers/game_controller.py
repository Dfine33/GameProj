import os
import json
import pygame
from src.eve.config import get_eve_menu_buttons
from src.eve.game import start_eve_game
from src.pve.config import get_pve_menu_buttons, get_team_select_buttons
from src.pve.game import start_pve_game

from src.views.pygame_view import Button
from src.utils.common import hex_neighbors, hex_distance
from src.core.balance import UNIT_STATS, UNIT_COSTS
from src.ai.policy import Action
from src.core.state import GameState

class GameController:
    def __init__(self, renderer, view):
        self.renderer = renderer
        self.view = view
        self.loop = start_eve_game(renderer) # Default to EVE loop or just any valid loop
        self.renderer.initialize(self.loop.state)
        self.state_view = 'MENU_ROOT'
        self.w, self.h = self.renderer.screen.get_size()
        self.view.init_menu_buttons(self.w)
        self.view.init_gameover_buttons(self.w)
        self.feed_items = []
        self.last_known = {'A': None, 'B': None}
        self.paused = False
        self.speed = 1.0
        self.sim_accum = 0.0
        self.step_mode = False
        self.do_step = False
        self.renderer.paused = self.paused
        self.renderer.speed = self.speed
        self.renderer.step_mode = self.step_mode
        self.map_select = []
        self.select_buttons = []
        self.initial_mode = 'random'
        self.initial_map_path = None
        self.mode_menu_state = None
        self.player_team = 'A'
        self.pending_start_mode = None
        self.pending_map_path = None
        self.ui_mode = None
        self.selected_base = None
        self.selected_unit = None

    def reset_runtime(self):
        self.feed_items = []
        self.last_known = {'A': None, 'B': None}
        self.paused = False
        self.speed = 1.0
        self.sim_accum = 0.0
        self.step_mode = False
        self.do_step = False
        self.renderer.paused = self.paused
        self.renderer.speed = self.speed
        self.renderer.step_mode = self.step_mode

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.renderer.running = False
            return
        if event.type == pygame.KEYDOWN:
            uni = (event.unicode or '').lower()
            if self.state_view == 'MENU_ROOT':
                if event.key == pygame.K_RETURN:
                    self.state_view = 'MENU_EVE'
                    configs = get_eve_menu_buttons(self.w)
                    self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                    self.view.menu_title = 'EVE 电脑对战'
                elif event.key == pygame.K_ESCAPE:
                    self.renderer.running = False
            elif self.state_view == 'MAP_SELECT':
                if event.key == pygame.K_ESCAPE:
                    self.state_view = getattr(self, 'prev_menu_state', 'MENU_ROOT')
            elif self.state_view == 'RUNNING':
                if event.key == pygame.K_ESCAPE:
                    if self.mode_menu_state == 'MENU_EVE':
                        configs = get_eve_menu_buttons(self.w)
                        self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                        self.view.menu_title = 'EVE 电脑对战'
                        self.state_view = 'MENU_EVE'
                    elif self.mode_menu_state == 'MENU_PVE':
                        configs = get_pve_menu_buttons(self.w)
                        self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                        self.view.menu_title = 'PVE 人机对战'
                        self.state_view = 'MENU_PVE'
                    else:
                        self.view.init_menu_buttons(self.w)
                        self.state_view = 'MENU_ROOT'
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    self.renderer.paused = self.paused
                elif event.key == pygame.K_LEFT:
                    self.speed = max(0.25, self.speed - 0.25)
                    self.renderer.speed = self.speed
                elif event.key == pygame.K_RIGHT:
                    self.speed = min(3.0, self.speed + 0.25)
                    self.renderer.speed = self.speed
                elif event.key == pygame.K_t or uni == 't':
                    self.step_mode = not self.step_mode
                    self.renderer.step_mode = self.step_mode
                elif event.key == pygame.K_n or uni == 'n':
                    self.do_step = True
                # PVE 仅显示玩家阵营视野，禁用 1/2/3 切换
                if self.mode_menu_state != 'MENU_PVE':
                    if event.key == pygame.K_1:
                        self.renderer.view_mode = 'A'
                    elif event.key == pygame.K_2:
                        self.renderer.view_mode = 'B'
                    elif event.key == pygame.K_3:
                        self.renderer.view_mode = 'ALL'
            elif self.state_view == 'GAMEOVER':
                if event.key == pygame.K_r:
                    self._restart_game()
                elif event.key == pygame.K_m:
                    self.loop = start_eve_game(self.renderer)
                    self.renderer.initialize(self.loop.state)
                    self.state_view = 'MENU'
                    self.reset_runtime()
                elif event.key == pygame.K_ESCAPE:
                    if self.mode_menu_state == 'MENU_EVE':
                        configs = get_eve_menu_buttons(self.w)
                        self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                        self.view.menu_title = 'EVE 电脑对战'
                        self.state_view = 'MENU_EVE'
                    elif self.mode_menu_state == 'MENU_PVE':
                        configs = get_pve_menu_buttons(self.w)
                        self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                        self.view.menu_title = 'PVE 人机对战'
                        self.state_view = 'MENU_PVE'
                    else:
                        self.view.init_menu_buttons(self.w)
                        self.state_view = 'MENU_ROOT'
        elif event.type == pygame.VIDEORESIZE:
            self.renderer.handle_resize(event.w, event.h, self.loop.state)
            self.w, self.h = self.renderer.screen.get_size()
            
            if self.state_view == 'MENU_ROOT':
                self.view.init_menu_buttons(self.w)
            elif self.state_view == 'MENU_EVE':
                configs = get_eve_menu_buttons(self.w)
                self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                self.view.menu_title = 'EVE 电脑对战'
            elif self.state_view == 'MENU_PVE':
                configs = get_pve_menu_buttons(self.w)
                self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                self.view.menu_title = 'PVE 人机对战'
            elif self.state_view == 'TEAM_SELECT':
                configs = get_team_select_buttons(self.w)
                self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                self.view.menu_title = '选择队伍'
            elif self.state_view == 'GAMEOVER':
                self.view.init_gameover_buttons(self.w)
            elif self.state_view == 'MAP_SELECT':
                self.select_buttons = self.view.make_select_buttons(self.w, self.map_select)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.state_view == 'MENU_ROOT':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'mode_eve':
                            self.state_view = 'MENU_EVE'
                            self.mode_menu_state = 'MENU_EVE'
                            configs = get_eve_menu_buttons(self.w)
                            self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                            self.view.menu_title = 'EVE 电脑对战'
                        elif b.action == 'mode_pve':
                            self.state_view = 'MENU_PVE'
                            self.mode_menu_state = 'MENU_PVE'
                            configs = get_pve_menu_buttons(self.w)
                            self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                            self.view.menu_title = 'PVE 人机对战'
                        elif b.action == 'mode_pvp':
                            w, h = self.renderer.screen.get_size()
                            self.view.push_feed(self.renderer, 'PVP 待拓展', w - 10, 6)
                        elif b.action == 'map_editor':
                            try:
                                import src.map_editor as map_editor
                                map_editor.main()
                                self.renderer.initialize(self.loop.state)
                            except Exception:
                                pass
                        elif b.action == 'debug_tool':
                            try:
                                from src.tools.vision_path_tester import main as tester_main
                                tester_main()
                                self.renderer.initialize(self.loop.state)
                            except Exception:
                                pass
                        elif b.action == 'quit':
                            self.renderer.running = False
            elif self.state_view == 'MENU_EVE':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'eve_random':
                            self.loop = start_eve_game(self.renderer)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'RUNNING'
                            self.initial_mode = 'random'
                            self.initial_map_path = None
                            self.mode_menu_state = 'MENU_EVE'
                            self.reset_runtime()
                        elif b.action == 'eve_select':
                            maps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'maps')
                            os.makedirs(maps_dir, exist_ok=True)
                            files = [f for f in os.listdir(maps_dir) if f.lower().endswith('.json')]
                            self.map_select = files
                            self.select_buttons = self.view.make_select_buttons(self.w, self.map_select)
                            self.prev_menu_state = 'MENU_EVE'
                            self.state_view = 'MAP_SELECT'
                        elif b.action == 'back_root':
                            self.state_view = 'MENU_ROOT'
                            self.view.init_menu_buttons(self.w)
            elif self.state_view == 'MENU_PVE':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'pve_random':
                            self.pending_start_mode = 'random'
                            self.pending_map_path = None
                            self.state_view = 'TEAM_SELECT'
                            configs = get_team_select_buttons(self.w)
                            self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                            self.view.menu_title = '选择队伍'
                        elif b.action == 'pve_select':
                            maps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'maps')
                            os.makedirs(maps_dir, exist_ok=True)
                            files = [f for f in os.listdir(maps_dir) if f.lower().endswith('.json')]
                            self.map_select = files
                            self.select_buttons = self.view.make_select_buttons(self.w, self.map_select)
                            self.prev_menu_state = 'MENU_PVE'
                            self.state_view = 'MAP_SELECT'
                        elif b.action == 'back_root':
                            self.state_view = 'MENU_ROOT'
                            self.view.init_menu_buttons(self.w)
            elif self.state_view == 'TEAM_SELECT':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'team_a':
                            self.player_team = 'A'
                            self._start_pve_from_pending()
                        elif b.action == 'team_b':
                            self.player_team = 'B'
                            self._start_pve_from_pending()
                        elif b.action == 'back_prev':
                            self.state_view = 'MENU_PVE'
                            configs = get_pve_menu_buttons(self.w)
                            self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                            self.view.menu_title = 'PVE 人机对战'
                        elif b.action == 'map_editor':
                            try:
                                import src.map_editor as map_editor
                                map_editor.main()
                                self.renderer.initialize(self.loop.state)
                            except Exception:
                                pass
                        elif b.action == 'quit':
                            self.renderer.running = False
            elif self.state_view == 'MAP_SELECT':
                for b in self.select_buttons:
                    if b.rect.collidepoint(event.pos):
                        name = b.action.split(':',1)[1]
                        try:
                            maps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'maps')
                            with open(os.path.join(maps_dir, name), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            st = GameState.deserialize(data)
                            if getattr(self, 'prev_menu_state', None) == 'MENU_PVE':
                                self.pending_start_mode = 'file'
                                self.pending_map_path = os.path.join(maps_dir, name)
                                self.state_view = 'TEAM_SELECT'
                                configs = get_team_select_buttons(self.w)
                                self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
                                self.view.menu_title = '选择队伍'
                            else:
                                self.loop = start_eve_game(self.renderer, initial_state=st)
                                self.renderer.initialize(self.loop.state)
                                self.state_view = 'RUNNING'
                                self.initial_mode = 'file'
                                self.initial_map_path = os.path.join(maps_dir, name)
                                # 从之前菜单状态推断当前模式菜单
                                self.mode_menu_state = getattr(self, 'prev_menu_state', None)
                                self.loop.await_human = False
                                self.renderer.view_mode = 'ALL'
                                self.reset_runtime()
                        except Exception as e:
                            print(f"Error loading map: {e}")
                            self.state_view = 'MENU_ROOT'
            elif self.state_view == 'RUNNING':
                r = self.renderer.ui_rects
                if r.get('pause') and r['pause'].collidepoint(event.pos):
                    self.paused = not self.paused
                    self.renderer.paused = self.paused
                elif r.get('speed_minus') and r['speed_minus'].collidepoint(event.pos):
                    self.speed = max(0.25, self.speed - 0.25)
                    self.renderer.speed = self.speed
                elif r.get('speed_plus') and r['speed_plus'].collidepoint(event.pos):
                    self.speed = min(3.0, self.speed + 0.25)
                    self.renderer.speed = self.speed
                elif r.get('step_mode') and r['step_mode'].collidepoint(event.pos):
                    self.step_mode = not self.step_mode
                    self.renderer.step_mode = self.step_mode
                elif r.get('step_once') and r['step_once'].collidepoint(event.pos):
                    self.do_step = True
                elif r.get('end_turn') and r['end_turn'].collidepoint(event.pos):
                    if self.mode_menu_state == 'MENU_PVE':
                        self.loop.human_ready = True
                        self.ui_mode = None
                        self.selected_base = None
                        self.selected_unit = None
                        self.renderer.ui_highlights = set()
                        self.renderer.path_preview = []
                        self.renderer.panel = None
                        self.renderer.preview_paths = {}
                        if self.step_mode:
                            self.do_step = True
                else:
                    # 面板按钮优先处理
                    pr = getattr(self.renderer, 'panel_rects', {})
                    if pr and self.ui_mode in ('BASE_PANEL','UNIT_PANEL'):
                        if self.ui_mode == 'BASE_PANEL':
                            for name in ('Scout','Infantry','Archer'):
                                r = pr.get(name)
                                if r and r.collidepoint(event.pos):
                                    self.recruit_kind = name
                                    self._open_recruit_panel()
                                    return
                            ur = pr.get('undo')
                            if ur and ur.collidepoint(event.pos):
                                self.loop.undo_last_recruit()
                                self._open_recruit_panel()
                                return
                        elif self.ui_mode == 'UNIT_PANEL':
                            if pr.get('unit_move') and pr['unit_move'].collidepoint(event.pos):
                                self.unit_mode = 'move'
                                self._open_unit_panel(self.selected_unit)
                                return
                            elif pr.get('unit_attack') and pr['unit_attack'].collidepoint(event.pos):
                                self.unit_mode = 'attack'
                                self._open_unit_panel(self.selected_unit)
                                return
                            elif pr.get('undo') and pr['undo'].collidepoint(event.pos):
                                self.loop.set_unit_action(self.selected_unit, Action('idle', None))
                                self.renderer.path_preview = []
                                self._open_unit_panel(self.selected_unit)
                                return
                    hx = getattr(self.renderer, 'pixel_to_hex', None)
                    if hx:
                        pos = hx(*event.pos)
                        if pos:
                            x, y = pos
                            # 选择玩家基地打开招募面板
                            base = self.loop.state.base_a if self.player_team=='A' else self.loop.state.base_b
                            if (x, y) == base.pos():
                                if self.ui_mode == 'BASE_PANEL' and self.selected_base is base:
                                    # toggle off
                                    self.ui_mode = None
                                    self.selected_base = None
                                    self.renderer.ui_highlights = set()
                                    self.renderer.path_preview = []
                                    self.renderer.panel = None
                                else:
                                    self.ui_mode = 'BASE_PANEL'
                                    self.selected_base = base
                                    self._open_recruit_panel()
                            else:
                                # 选择玩家单位打开控制面板
                                unit = next((u for u in self.loop.state.units if (u.x, u.y)==(x, y) and u.team==self.player_team), None)
                                if unit:
                                    if self.ui_mode == 'UNIT_PANEL' and self.selected_unit is unit:
                                        # toggle off
                                        self.ui_mode = None
                                        self.selected_unit = None
                                        self.renderer.ui_highlights = set()
                                        self.renderer.path_preview = []
                                        self.renderer.panel = None
                                    else:
                                        self.ui_mode = 'UNIT_PANEL'
                                        self.selected_unit = unit
                                        self._open_unit_panel(unit)
                                else:
                                    # 放置或移动/攻击执行
                                    self._handle_map_click(x, y)
            elif self.state_view == 'GAMEOVER':
                for b in self.view.gameover_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'restart':
                            self._restart_game()
                        elif b.action == 'menu':
                            self.loop = start_eve_game(self.renderer)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'MENU'
                            self.reset_runtime()
    def _restart_game(self):
        if self.mode_menu_state == 'MENU_PVE':
            self.pending_start_mode = self.initial_mode
            self.pending_map_path = self.initial_map_path
            self.state_view = 'TEAM_SELECT'
            configs = get_team_select_buttons(self.w)
            self.view.menu_buttons = [Button(c.rect, c.label, c.action) for c in configs]
            self.view.menu_title = '选择队伍'
            return
        if self.initial_mode == 'file' and self.initial_map_path and os.path.exists(self.initial_map_path):
            try:
                with open(self.initial_map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                st = GameState.deserialize(data)
                self.loop = start_eve_game(self.renderer, initial_state=st)
            except Exception:
                self.loop = start_eve_game(self.renderer)
        else:
            self.loop = start_eve_game(self.renderer)
        self.renderer.initialize(self.loop.state)
        self.state_view = 'RUNNING'
        self.reset_runtime()

    def _start_pve_from_pending(self):
        if self.pending_start_mode == 'file' and self.pending_map_path and os.path.exists(self.pending_map_path):
            with open(self.pending_map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            st = GameState.deserialize(data)
            self.loop = start_pve_game(self.renderer, initial_state=st)
            self.initial_mode = 'file'
            self.initial_map_path = self.pending_map_path
        else:
            self.loop = start_pve_game(self.renderer)
            self.initial_mode = 'random'
            self.initial_map_path = None
        self.renderer.initialize(self.loop.state)
        self.mode_menu_state = 'MENU_PVE'
        self.loop.await_human = True
        self.loop.human_ready = False
        self.loop.player_team = self.player_team
        self.loop.start_player_phase()
        self.renderer.view_mode = self.player_team
        self.state_view = 'RUNNING'
        self.reset_runtime()
        # Default to frame/step mode for PVE
        self.step_mode = True
        self.renderer.step_mode = True

    def tick_step(self):
        # 更新操作阶段的预览数据（每帧）
        self.renderer.preview_recruits = list(getattr(self.loop, 'player_recruits', []))
        self.renderer.preview_actions = dict(getattr(self.loop, 'player_actions', {}))
        if self.step_mode:
            if self.do_step:
                cont = self.loop.step(print_every=1)
                self.do_step = False
            else:
                self.renderer.render(self.loop.state, self.loop.state.tick)
                cont = True
        else:
            if self.paused:
                self.renderer.render(self.loop.state, self.loop.state.tick)
                cont = True
            else:
                self.sim_accum += self.speed
                steps = int(self.sim_accum)
                steps = max(1, min(steps, 5))
                cont = True
                for _ in range(steps):
                    cont = self.loop.step(print_every=1)
                    self.sim_accum -= 1
                    if not cont:
                        break
        for side in ['A','B']:
            cur = self.loop.state.known_enemy_base.get(side)
            if self.last_known.get(side) is None and cur is not None:
                w, h = self.renderer.screen.get_size()
                y = 6 + (0 if side == 'A' else 18)
                self.view.push_feed(self.renderer, f"{side} 发现敌方基地", w - 10, y)
                self.last_known[side] = cur
        if not cont:
            self.state_view = 'GAMEOVER'

    def run(self):
        while self.renderer.running:
            mx, my = pygame.mouse.get_pos()
            self.view.update_hover(self.renderer, mx, my, self.select_buttons)
            for event in pygame.event.get():
                self.handle_event(event)
            if self.state_view in ('MENU_ROOT','MENU_EVE','MENU_PVE'):
                self.view.draw_menu(self.renderer)
            elif self.state_view == 'TEAM_SELECT':
                self.view.draw_menu(self.renderer)
            elif self.state_view == 'MAP_SELECT':
                self.view.draw_select(self.renderer, self.select_buttons)
            elif self.state_view == 'RUNNING':
                self.tick_step()
            elif self.state_view == 'GAMEOVER':
                self.view.draw_gameover(self.renderer, self.loop.state)
            self.view.update_feed(self.renderer)
            self.renderer.clock.tick(self.renderer.fps)

    def _open_recruit_panel(self):
        # 高亮基地周围可放置格
        base = self.selected_base
        nbrs = [p for p in hex_neighbors(base.x, base.y)]
        hl = set()
        for x, y in nbrs:
            if self.loop.state.map.in_bounds(x, y) and self.loop.state.map.can_walk(x, y) and (x, y) not in self.loop.state.occupied:
                hl.add((x, y))
        self.renderer.ui_highlights = hl
        self.renderer.path_preview = []
        items = []
        for name in ('Scout','Infantry','Archer'):
            st = UNIT_STATS[name]
            items.append({'name': name, 'cost': UNIT_COSTS[name], 'atk': st['atk'], 'hp': st['hp'], 'spd': st['spd']})
        pts = self.loop.player_points
        self.renderer.panel = {'type':'base','title':'招募', 'points': pts, 'items': items, 'selected_item': getattr(self, 'recruit_kind', None)}

    def _open_unit_panel(self, unit):
        # 高亮可达位置（速度步数），简单一圈邻居扩展
        frontier = [(unit.x, unit.y, 0)]
        seen = {(unit.x, unit.y)}
        hl = set()
        while frontier:
            x, y, d = frontier.pop(0)
            if d >= unit.spd:
                continue
            for nx, ny in hex_neighbors(x, y):
                if not self.loop.state.map.in_bounds(nx, ny):
                    continue
                if (nx, ny) in seen:
                    continue
                if self.loop._is_known_walkable(self.player_team, nx, ny) and (nx, ny) not in self.loop.state.occupied:
                    seen.add((nx, ny))
                    hl.add((nx, ny))
                    frontier.append((nx, ny, d+1))
        self.renderer.ui_highlights = hl
        self.renderer.path_preview = []
        # 目标列表（攻击范围内）
        targets = []
        for e in self.loop.state.units + [self.loop.state.base_a, self.loop.state.base_b]:
            if getattr(e, 'team', unit.team) != unit.team and hex_distance(unit.pos(), e.pos()) <= unit.rng:
                targets.append(e)
        self.unit_mode = getattr(self, 'unit_mode', 'move')
        self.renderer.panel = {'type':'unit','title':'单位操作','unit':unit, 'max_hp': unit.hp, 'targets': targets, 'selected_mode': self.unit_mode}

    def _handle_map_click(self, x, y):
        if self.ui_mode == 'BASE_PANEL' and self.selected_base:
            # 默认招募步兵示例，可扩展三个按钮（此处简化成单类型演示）
            kind = getattr(self, 'recruit_kind', 'Infantry')
            if (x, y) in getattr(self.renderer, 'ui_highlights', set()) and self.loop.can_recruit(kind):
                ok = self.loop.queue_recruit(self.selected_base, kind, (x, y))
                if ok:
                    self.renderer.ui_highlights.remove((x, y))
                    self._open_recruit_panel()
        elif self.ui_mode == 'UNIT_PANEL' and self.selected_unit:
            # 移动选择
            if (x, y) in getattr(self.renderer, 'ui_highlights', set()):
                self.loop.set_unit_action(self.selected_unit, Action('move_towards', (x, y)))
                self.renderer.path_preview = [(self.selected_unit.x, self.selected_unit.y), (x, y)]
            # 攻击选择：点击敌方单位或基地（列表也可选）
            else:
                for e in self.loop.state.units + [self.loop.state.base_a, self.loop.state.base_b]:
                    if getattr(e, 'team', self.player_team) != self.player_team and (e.x, e.y)==(x, y):
                        if hex_distance(self.selected_unit.pos(), e.pos()) <= self.selected_unit.rng:
                            self.loop.set_unit_action(self.selected_unit, Action('attack', e))
                            self.renderer.path_preview = []
                            self._open_unit_panel(self.selected_unit)
        # 更新移动预览路径（基于真实可走路径）
        if self.ui_mode == 'UNIT_PANEL' and self.selected_unit and self.unit_mode == 'move':
            path = self.loop.preview_path(self.selected_unit, (x, y))
            if path:
                # 限制到本回合移动范围
                max_len = min(len(path), self.selected_unit.spd + 1)
                trunc = path[:max_len]
                if len(trunc) > 1:
                    self.loop.set_unit_action(self.selected_unit, Action('move_path', trunc))
                    self.renderer.preview_actions[self.selected_unit] = Action('move_path', None)
                    self.renderer.preview_paths[self.selected_unit] = trunc
                # 用路径替换 path_preview 的线渲染由 renderer.preview_actions 分支完成
                self.renderer.path_preview = []  # 确保不绘制直线
