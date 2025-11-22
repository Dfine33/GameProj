class Base:
    def __init__(self, team, x, y, hp):
        self.team = team
        self.x = x
        self.y = y
        self.hp = hp
        self.spawn_cooldown = 0

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