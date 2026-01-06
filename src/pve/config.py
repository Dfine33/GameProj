from collections import namedtuple
import pygame

class ButtonConfig:
    def __init__(self, rect_tuple, label, action):
        self.rect = pygame.Rect(rect_tuple)
        self.label = label
        self.action = action
        self.hover = False

def get_pve_menu_buttons(w):
    return [
        ButtonConfig((w//2-100, 190, 200, 36), '随机地图', 'pve_random'),
        ButtonConfig((w//2-100, 236, 200, 36), '选择地图', 'pve_select'),
        ButtonConfig((w//2-100, 282, 200, 36), '返回主菜单', 'back_root'),
    ]

def get_team_select_buttons(w):
    return [
        ButtonConfig((w//2-100, 190, 200, 36), '红队 (A)', 'team_a'),
        ButtonConfig((w//2-100, 236, 200, 36), '蓝队 (B)', 'team_b'),
        ButtonConfig((w//2-100, 282, 200, 36), '返回上一级', 'back_prev'),
    ]
