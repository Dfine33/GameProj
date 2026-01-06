class Base:
    def __init__(self, team, x, y, hp, build_points_per_turn=None, build_point_bonus=0):
        self.team = team
        self.x = x
        self.y = y
        self.hp = hp
        self.spawn_cooldown = 0
        self.build_points_per_turn = build_points_per_turn
        self.build_point_bonus = build_point_bonus

    def pos(self):
        return self.x, self.y

class Unit:
    def __init__(self, team, kind, x, y, atk, rng, spd, hp, armor, vision):
        self.team = team
        self.kind = kind
        self.x = x
        self.y = y
        self.atk = atk
        self.rng = rng
        self.spd = spd
        self.hp = hp
        self.armor = armor
        self.vision = vision

    def pos(self):
        return self.x, self.y
