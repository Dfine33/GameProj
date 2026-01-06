from collections import namedtuple
import pygame

class ButtonConfig:
    def __init__(self, rect_tuple, label, action):
        self.rect = pygame.Rect(rect_tuple)
        self.label = label
        self.action = action
        self.hover = False

def get_eve_menu_buttons(w):
    return [
        ButtonConfig((w//2-100, 190, 200, 36), '随机地图', 'eve_random'),
        ButtonConfig((w//2-100, 236, 200, 36), '选择地图', 'eve_select'),
        ButtonConfig((w//2-100, 282, 200, 36), '返回主菜单', 'back_root'),
    ]
