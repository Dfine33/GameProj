import pygame
from simulation.loop import SimulationLoop
from ai.policy import TwoPhasePolicy
from renderer.pygame_renderer import PygameRenderer

def draw_center_text(screen, font, text, y, color):
    w, h = screen.get_size()
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(w//2, y))
    screen.blit(surf, rect.topleft)

class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.hover = False

    def draw(self, screen, font):
        base = (40, 40, 48)
        hilite = (70, 70, 90)
        color = hilite if self.hover else base
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (110,110,130), self.rect, 2)
        surf = font.render(self.label, True, (230,230,230))
        srect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, srect.topleft)

class FeedItem:
    def __init__(self, text, x, y, speed=2.0, ttl=600):
        self.text = text
        self.x = x
        self.y = y
        self.speed = speed
        self.ttl = ttl

    def update(self):
        self.x -= self.speed
        self.ttl -= 1

    def alive(self, w):
        return self.ttl > 0 and self.x > -w

def draw_menu(renderer):
    renderer.screen.fill((20,20,24))
    draw_center_text(renderer.screen, renderer.title_font, 'RTS 模拟', 120, (240,240,240))
    for b in renderer.menu_buttons:
        b.draw(renderer.screen, renderer.font)
    pygame.display.flip()

def compute_winner(state):
    if state.base_a.hp <= 0 and state.base_b.hp <= 0:
        return '平局'
    if state.base_a.hp <= 0:
        return '乙方'
    if state.base_b.hp <= 0:
        return '甲方'
    return '未分胜负'

def draw_gameover(renderer, state, winner):
    renderer.screen.fill((12,12,16))
    draw_center_text(renderer.screen, renderer.title_font, f'结果 {winner}', 140, (240,240,240))
    a_cnt = sum(1 for u in state.units if u.team=='A')
    b_cnt = sum(1 for u in state.units if u.team=='B')
    draw_center_text(renderer.screen, renderer.font, f'Tick {state.tick}  单位 A {a_cnt} / B {b_cnt}', 180, (200,200,200))
    for b in renderer.gameover_buttons:
        b.draw(renderer.screen, renderer.font)
    pygame.display.flip()

def update_feed(renderer):
    w, h = renderer.screen.get_size()
    nf = []
    for it in getattr(renderer, 'feed_items', []):
        it.update()
        if it.alive(w):
            nf.append(it)
    renderer.feed_items = nf

def draw_feed(renderer):
    for it in getattr(renderer, 'feed_items', []):
        surf = renderer.font.render(it.text, True, (240, 220, 80))
        renderer.screen.blit(surf, (int(it.x), int(it.y)))

def main():
    renderer = PygameRenderer()
    loop = SimulationLoop(TwoPhasePolicy(), renderer)
    renderer.initialize(loop.state)
    w, h = renderer.screen.get_size()
    renderer.menu_buttons = [
        Button((w//2-80, 180, 160, 36), '开始', 'start'),
        Button((w//2-80, 226, 160, 36), '退出', 'quit'),
    ]
    renderer.gameover_buttons = [
        Button((w//2-180, 230, 160, 36), '重开', 'restart'),
        Button((w//2+20, 230, 160, 36), '主菜单', 'menu'),
    ]
    state_view = 'MENU'
    winner = None
    renderer.feed_items = []
    last_known = {'A': None, 'B': None}
    paused = False
    speed = 1.0
    sim_accum = 0.0
    renderer.paused = paused
    renderer.speed = speed
    while renderer.running:
        mx, my = pygame.mouse.get_pos()
        for b in renderer.menu_buttons:
            b.hover = b.rect.collidepoint(mx, my)
        for b in renderer.gameover_buttons:
            b.hover = b.rect.collidepoint(mx, my)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False
            elif event.type == pygame.KEYDOWN:
                if state_view == 'MENU':
                    if event.key == pygame.K_RETURN:
                        state_view = 'RUNNING'
                    elif event.key == pygame.K_ESCAPE:
                        renderer.running = False
                elif state_view == 'RUNNING':
                    if event.key == pygame.K_ESCAPE:
                        state_view = 'MENU'
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                        renderer.paused = paused
                    elif event.key == pygame.K_LEFT:
                        speed = max(0.25, speed - 0.25)
                        renderer.speed = speed
                    elif event.key == pygame.K_RIGHT:
                        speed = min(3.0, speed + 0.25)
                        renderer.speed = speed
                elif state_view == 'GAMEOVER':
                    if event.key == pygame.K_r:
                        loop = SimulationLoop(TwoPhasePolicy(), renderer)
                        renderer.initialize(loop.state)
                        state_view = 'RUNNING'
                        winner = None
                    elif event.key == pygame.K_m:
                        loop = SimulationLoop(TwoPhasePolicy(), renderer)
                        renderer.initialize(loop.state)
                        state_view = 'MENU'
                        winner = None
                    elif event.key == pygame.K_ESCAPE:
                        renderer.running = False
                if event.key == pygame.K_1:
                    renderer.view_mode = 'A'
                elif event.key == pygame.K_2:
                    renderer.view_mode = 'B'
                elif event.key == pygame.K_3:
                    renderer.view_mode = 'ALL'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state_view == 'MENU':
                    for b in renderer.menu_buttons:
                        if b.rect.collidepoint(event.pos):
                            if b.action == 'start':
                                state_view = 'RUNNING'
                            elif b.action == 'quit':
                                renderer.running = False
                elif state_view == 'GAMEOVER':
                    for b in renderer.gameover_buttons:
                        if b.rect.collidepoint(event.pos):
                            if b.action == 'restart':
                                loop = SimulationLoop(TwoPhasePolicy(), renderer)
                                renderer.initialize(loop.state)
                                state_view = 'RUNNING'
                                winner = None
                            elif b.action == 'menu':
                                loop = SimulationLoop(TwoPhasePolicy(), renderer)
                                renderer.initialize(loop.state)
                                state_view = 'MENU'
                                winner = None
                elif state_view == 'RUNNING':
                    r = renderer.ui_rects
                    if r.get('pause') and r['pause'].collidepoint(event.pos):
                        paused = not paused
                        renderer.paused = paused
                    elif r.get('speed_minus') and r['speed_minus'].collidepoint(event.pos):
                        speed = max(0.25, speed - 0.25)
                        renderer.speed = speed
                    elif r.get('speed_plus') and r['speed_plus'].collidepoint(event.pos):
                        speed = min(3.0, speed + 0.25)
                        renderer.speed = speed
        if state_view == 'MENU':
            draw_menu(renderer)
        elif state_view == 'RUNNING':
            if paused:
                renderer.render(loop.state, loop.state.tick)
                cont = True
            else:
                sim_accum += speed
                steps = int(sim_accum)
                steps = max(1, min(steps, 5))
                cont = True
                for _ in range(steps):
                    cont = loop.step(print_every=1)
                    sim_accum -= 1
                    if not cont:
                        break
            for side in ['A','B']:
                cur = loop.state.known_enemy_base.get(side)
                if last_known.get(side) is None and cur is not None:
                    w, h = renderer.screen.get_size()
                    y = 6 + (0 if side == 'A' else 18)
                    renderer.feed_items.append(FeedItem(f"{side} 发现敌方基地", w - 10, y, speed=3.0, ttl=500))
                    last_known[side] = cur
            if not cont:
                winner = compute_winner(loop.state)
                state_view = 'GAMEOVER'
            else:
                pass
        elif state_view == 'GAMEOVER':
            draw_gameover(renderer, loop.state, winner)
        update_feed(renderer)
        renderer.clock.tick(renderer.fps)
    renderer.close()

if __name__ == '__main__':
    main()