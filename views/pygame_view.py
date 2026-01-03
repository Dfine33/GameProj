import pygame

class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.hover = False
        self.selected = False

    def draw(self, screen, font):
        base = (40, 40, 48)
        hilite = (70, 70, 90)
        sel = (90, 90, 110)
        color = sel if self.selected else (hilite if self.hover else base)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        border_col = (240,220,80) if self.selected else (110,110,130)
        pygame.draw.rect(screen, border_col, self.rect, 3 if self.selected else 2, border_radius=4)
        surf = font.render(self.label, True, (230,230,230))
        srect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, srect.topleft)

class PygameView:
    def __init__(self):
        self.menu_buttons = []
        self.gameover_buttons = []
        self.menu_title = '主菜单'

    def draw_center_text(self, screen, font, text, y, color):
        w, h = screen.get_size()
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(w//2, y))
        screen.blit(surf, rect.topleft)

    def init_menu_buttons(self, w):
        self.menu_title = '主菜单'
        self.menu_buttons = [
            Button((w//2-100, 170, 200, 36), 'EVE 电脑对战', 'mode_eve'),
            Button((w//2-100, 216, 200, 36), 'PVE 人机对战', 'mode_pve'),
            Button((w//2-100, 262, 200, 36), 'PVP 网络对战', 'mode_pvp'),
            Button((w//2-100, 308, 200, 36), '地图编辑器', 'map_editor'),
            Button((w//2-100, 354, 200, 36), '调试工具', 'debug_tool'),
            Button((w//2-100, 400, 200, 36), '退出', 'quit'),
        ]

    def init_eve_buttons(self, w):
        self.menu_title = 'EVE 电脑对战'
        self.menu_buttons = [
            Button((w//2-100, 190, 200, 36), '随机地图', 'eve_random'),
            Button((w//2-100, 236, 200, 36), '选择地图', 'eve_select'),
            Button((w//2-100, 282, 200, 36), '返回主菜单', 'back_root'),
        ]

    def init_pve_buttons(self, w):
        self.menu_title = 'PVE 人机对战'
        self.menu_buttons = [
            Button((w//2-100, 190, 200, 36), '随机地图', 'pve_random'),
            Button((w//2-100, 236, 200, 36), '选择地图', 'pve_select'),
            Button((w//2-100, 282, 200, 36), '返回主菜单', 'back_root'),
        ]

    def init_team_select_buttons(self, w):
        self.menu_title = '选择队伍'
        self.menu_buttons = [
            Button((w//2-100, 190, 200, 36), '红队 (A)', 'team_a'),
            Button((w//2-100, 236, 200, 36), '蓝队 (B)', 'team_b'),
            Button((w//2-100, 282, 200, 36), '返回上一级', 'back_prev'),
        ]

    def init_gameover_buttons(self, w):
        self.gameover_buttons = [
            Button((w//2-180, 230, 160, 36), '重开', 'restart'),
            Button((w//2+20, 230, 160, 36), '主菜单', 'menu'),
        ]

    def make_select_buttons(self, w, names):
        x0 = w//2 - 220
        y0 = 180
        y = y0
        res = []
        for name in names[:10]:
            res.append(Button((x0, y, 440, 30), name, f'select:{name}'))
            y += 36
        return res

    def draw_menu(self, renderer):
        renderer.screen.fill((20,20,24))
        self.draw_center_text(renderer.screen, renderer.title_font, self.menu_title, 120, (240,240,240))
        for b in self.menu_buttons:
            b.draw(renderer.screen, renderer.font)
        pygame.display.flip()

    def draw_select(self, renderer, buttons):
        renderer.screen.fill((20,20,24))
        self.draw_center_text(renderer.screen, renderer.title_font, '选择地图', 120, (240,240,240))
        for b in buttons:
            b.draw(renderer.screen, renderer.font)
        pygame.display.flip()

    def draw_gameover(self, renderer, state):
        renderer.screen.fill((12,12,16))
        self.draw_center_text(renderer.screen, renderer.title_font, f'结果 未分胜负' if state.base_a.hp>0 and state.base_b.hp>0 else ('结果 乙方' if state.base_a.hp<=0 else '结果 甲方'), 140, (240,240,240))
        a_cnt = sum(1 for u in state.units if u.team=='A')
        b_cnt = sum(1 for u in state.units if u.team=='B')
        self.draw_center_text(renderer.screen, renderer.font, f'Tick {state.tick}  单位 A {a_cnt} / B {b_cnt}', 180, (200,200,200))
        for b in self.gameover_buttons:
            b.draw(renderer.screen, renderer.font)
        pygame.display.flip()

    def update_hover(self, renderer, mx, my, select_buttons):
        for b in self.menu_buttons:
            b.hover = b.rect.collidepoint(mx, my)
        for b in self.gameover_buttons:
            b.hover = b.rect.collidepoint(mx, my)
        for b in select_buttons:
            b.hover = b.rect.collidepoint(mx, my)

    def push_feed(self, renderer, text, x, y):
        it = type('Feed', (), {})()
        it.text = text
        it.x = x
        it.y = y
        it.speed = 3.0
        it.ttl = 500
        if not hasattr(renderer, 'feed_items'):
            renderer.feed_items = []
        renderer.feed_items.append(it)

    def update_feed(self, renderer):
        w, h = renderer.screen.get_size()
        nf = []
        for it in getattr(renderer, 'feed_items', []):
            it.x -= it.speed
            it.ttl -= 1
            if it.ttl > 0 and it.x > -w:
                nf.append(it)
        renderer.feed_items = nf
