import pygame

class ButtonConfig:
    def __init__(self, rect_tuple, label, action):
        self.rect = pygame.Rect(rect_tuple)
        self.label = label
        self.action = action
        self.hover = False

def get_pvp_menu_buttons(w):
    return [
        ButtonConfig((w//2-100, 190, 200, 36), '创建房间 (主机)', 'pvp_host'),
        ButtonConfig((w//2-100, 236, 200, 36), '加入房间 (客机)', 'pvp_join'),
        ButtonConfig((w//2-100, 282, 200, 36), '返回主菜单', 'back_root'),
    ]

def get_pvp_host_map_buttons(w):
    return [
        ButtonConfig((w//2-100, 190, 200, 36), '随机地图', 'pvp_map_random'),
        ButtonConfig((w//2-100, 236, 200, 36), '选择地图文件', 'pvp_map_select'),
        ButtonConfig((w//2-100, 282, 200, 36), '返回', 'pvp_back_to_menu'),
    ]

def get_pvp_team_select_buttons(w):
    return [
        ButtonConfig((w//2-220, 200, 200, 60), '加入 红方 (A)', 'pvp_team_a'),
        ButtonConfig((w//2+20, 200, 200, 60), '加入 蓝方 (B)', 'pvp_team_b'),
        ButtonConfig((w//2-100, 300, 200, 36), '返回', 'pvp_back_to_map'),
    ]

def get_pvp_connect_buttons(w):
    # Just a connect/start button, input handled separately
    return [
        ButtonConfig((w//2-100, 280, 200, 36), '连接 / 开始', 'pvp_connect'),
        ButtonConfig((w//2-100, 326, 200, 36), '返回', 'pvp_back'),
    ]
