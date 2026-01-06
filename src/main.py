import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame
import json
from src.simulation.loop import SimulationLoop
from src.ai.policy import TwoPhasePolicy
from src.renderer.pygame_renderer import PygameRenderer
from src.controllers.game_controller import GameController
from src.views.pygame_view import PygameView
from src.ai.unit_policies import CompositePolicy
from src.core.state import GameState

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

def run_mvc():
    renderer = PygameRenderer()
    view = PygameView()
    controller = GameController(renderer, view)
    controller.loop.policy = CompositePolicy()
    controller.run()
    renderer.close()

if __name__ == '__main__':
    run_mvc()
