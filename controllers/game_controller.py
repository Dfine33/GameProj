import os
import json
import pygame
from simulation.loop import SimulationLoop
from core.state import GameState
from ai.unit_policies import CompositePolicy

class GameController:
    def __init__(self, renderer, view):
        self.renderer = renderer
        self.view = view
        self.loop = SimulationLoop(CompositePolicy(), renderer)
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
                    self.view.init_eve_buttons(self.w)
                elif event.key == pygame.K_ESCAPE:
                    self.renderer.running = False
            elif self.state_view == 'MAP_SELECT':
                if event.key == pygame.K_ESCAPE:
                    self.state_view = getattr(self, 'prev_menu_state', 'MENU_ROOT')
            elif self.state_view == 'RUNNING':
                if event.key == pygame.K_ESCAPE:
                    if self.mode_menu_state == 'MENU_EVE':
                        self.view.init_eve_buttons(self.w)
                        self.state_view = 'MENU_EVE'
                    elif self.mode_menu_state == 'MENU_PVE':
                        self.view.init_pve_buttons(self.w)
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
                    self.loop = SimulationLoop(CompositePolicy(), self.renderer)
                    self.renderer.initialize(self.loop.state)
                    self.state_view = 'MENU'
                    self.reset_runtime()
                elif event.key == pygame.K_ESCAPE:
                    if self.mode_menu_state == 'MENU_EVE':
                        self.view.init_eve_buttons(self.w)
                        self.state_view = 'MENU_EVE'
                    elif self.mode_menu_state == 'MENU_PVE':
                        self.view.init_pve_buttons(self.w)
                        self.state_view = 'MENU_PVE'
                    else:
                        self.view.init_menu_buttons(self.w)
                        self.state_view = 'MENU_ROOT'
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.state_view == 'MENU_ROOT':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'mode_eve':
                            self.state_view = 'MENU_EVE'
                            self.mode_menu_state = 'MENU_EVE'
                            self.view.init_eve_buttons(self.w)
                        elif b.action == 'mode_pve':
                            self.state_view = 'MENU_PVE'
                            self.mode_menu_state = 'MENU_PVE'
                            self.view.init_pve_buttons(self.w)
                        elif b.action == 'mode_pvp':
                            w, h = self.renderer.screen.get_size()
                            self.view.push_feed(self.renderer, 'PVP 待拓展', w - 10, 6)
                        elif b.action == 'map_editor':
                            try:
                                import map_editor
                                map_editor.main()
                                self.renderer.initialize(self.loop.state)
                            except Exception:
                                pass
                        elif b.action == 'quit':
                            self.renderer.running = False
            elif self.state_view == 'MENU_EVE':
                for b in self.view.menu_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'eve_random':
                            self.loop = SimulationLoop(CompositePolicy(), self.renderer)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'RUNNING'
                            self.initial_mode = 'random'
                            self.initial_map_path = None
                            self.mode_menu_state = 'MENU_EVE'
                            self.reset_runtime()
                        elif b.action == 'eve_select':
                            os.makedirs('maps', exist_ok=True)
                            files = [f for f in os.listdir('maps') if f.lower().endswith('.json')]
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
                            self.loop = SimulationLoop(CompositePolicy(), self.renderer)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'RUNNING'
                            self.initial_mode = 'random'
                            self.initial_map_path = None
                            self.mode_menu_state = 'MENU_PVE'
                            self.reset_runtime()
                        elif b.action == 'pve_select':
                            os.makedirs('maps', exist_ok=True)
                            files = [f for f in os.listdir('maps') if f.lower().endswith('.json')]
                            self.map_select = files
                            self.select_buttons = self.view.make_select_buttons(self.w, self.map_select)
                            self.prev_menu_state = 'MENU_PVE'
                            self.state_view = 'MAP_SELECT'
                        elif b.action == 'back_root':
                            self.state_view = 'MENU_ROOT'
                            self.view.init_menu_buttons(self.w)
                        elif b.action == 'map_editor':
                            try:
                                import map_editor
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
                            with open(os.path.join('maps', name), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            st = GameState.deserialize(data)
                            self.loop = SimulationLoop(CompositePolicy(), self.renderer, initial_state=st)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'RUNNING'
                            self.initial_mode = 'file'
                            self.initial_map_path = os.path.join('maps', name)
                            # 从之前菜单状态推断当前模式菜单
                            self.mode_menu_state = getattr(self, 'prev_menu_state', None)
                            self.reset_runtime()
                        except Exception:
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
            elif self.state_view == 'GAMEOVER':
                for b in self.view.gameover_buttons:
                    if b.rect.collidepoint(event.pos):
                        if b.action == 'restart':
                            self._restart_game()
                        elif b.action == 'menu':
                            self.loop = SimulationLoop(CompositePolicy(), self.renderer)
                            self.renderer.initialize(self.loop.state)
                            self.state_view = 'MENU'
                            self.reset_runtime()
    def _restart_game(self):
        if self.initial_mode == 'file' and self.initial_map_path and os.path.exists(self.initial_map_path):
            try:
                with open(self.initial_map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                st = GameState.deserialize(data)
                self.loop = SimulationLoop(CompositePolicy(), self.renderer, initial_state=st)
            except Exception:
                self.loop = SimulationLoop(CompositePolicy(), self.renderer)
        else:
            self.loop = SimulationLoop(CompositePolicy(), self.renderer)
        self.renderer.initialize(self.loop.state)
        self.state_view = 'RUNNING'
        self.reset_runtime()

    def tick_step(self):
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
            elif self.state_view == 'MAP_SELECT':
                self.view.draw_select(self.renderer, self.select_buttons)
            elif self.state_view == 'RUNNING':
                self.tick_step()
            elif self.state_view == 'GAMEOVER':
                self.view.draw_gameover(self.renderer, self.loop.state)
            self.view.update_feed(self.renderer)
            self.renderer.clock.tick(self.renderer.fps)
