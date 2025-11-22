import random
from core.entities import Base, Unit
from core.map import Map, generate
from core.map import PLAIN
from utils.common import manhattan, adjacent_positions

class GameState:
    def __init__(self, width=40, height=20):
        self.map = generate(width, height)
        self.base_a, self.base_b = self.place_bases()
        self.units = []
        self.occupied = set()
        self.tick = 0
        self.actions = []
        self.known_enemy_base = {'A': None, 'B': None}

    def update_occupied(self):
        self.occupied = set(u.pos() for u in self.units)

    def add_unit(self, u):
        self.units.append(u)
        self.update_occupied()

    def remove_unit(self, u):
        self.units = [x for x in self.units if x is not u]
        self.update_occupied()

    def serialize(self):
        return {
            'tick': self.tick,
            'map': {'width': self.map.width, 'height': self.map.height, 'grid': self.map.grid},
            'bases': [
                {'team': self.base_a.team, 'x': self.base_a.x, 'y': self.base_a.y, 'hp': self.base_a.hp},
                {'team': self.base_b.team, 'x': self.base_b.x, 'y': self.base_b.y, 'hp': self.base_b.hp}
            ],
            'units': [
                {'team': u.team, 'kind': u.kind, 'x': u.x, 'y': u.y, 'atk': u.atk, 'rng': u.rng, 'spd': u.spd, 'hp': u.hp, 'armor': u.armor, 'vision': u.vision}
                for u in self.units
            ],
            'known_enemy_base': self.known_enemy_base
        }

    @staticmethod
    def deserialize(data):
        mdata = data.get('map', {})
        m = Map(mdata.get('width', 40), mdata.get('height', 20))
        grid = mdata.get('grid')
        if grid:
            m.grid = grid
        gs = GameState(m.width, m.height)
        gs.map = m
        bases = data.get('bases', [])
        if len(bases) >= 2:
            a = bases[0]
            b = bases[1]
            gs.base_a = Base(a.get('team','A'), a.get('x',1), a.get('y',1), a.get('hp',500))
            gs.base_b = Base(b.get('team','B'), b.get('x',m.width-2), b.get('y',m.height-2), b.get('hp',500))
        gs.units = []
        for ud in data.get('units', []):
            gs.units.append(Unit(ud.get('team','A'), ud.get('kind','Infantry'), ud.get('x',0), ud.get('y',0), ud.get('atk',10), ud.get('rng',1), ud.get('spd',1), ud.get('hp',50), ud.get('armor',0), ud.get('vision',6)))
        gs.tick = data.get('tick', 0)
        keb = data.get('known_enemy_base')
        if isinstance(keb, dict):
            gs.known_enemy_base = {'A': keb.get('A'), 'B': keb.get('B')}
        gs.update_occupied()
        return gs

    def record_enemy_base(self, side, pos):
        self.known_enemy_base[side] = pos

    def find_open(self, preferred):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                x = preferred[0] + dx
                y = preferred[1] + dy
                if self.map.in_bounds(x, y) and self.map.grid[y][x] == PLAIN:
                    return x, y
        for y in range(self.map.height):
            for x in range(self.map.width):
                if self.map.grid[y][x] == PLAIN:
                    return x, y
        return None

    def place_bases(self):
        a = self.find_open((1, 1))
        b = self.find_open((self.map.width-2, self.map.height-2))
        return Base('A', a[0], a[1], 500), Base('B', b[0], b[1], 500)

    def spawn_unit(self, team, pos):
        k = random.choice(['Infantry','Archer','Cavalry'])
        if k == 'Infantry':
            return Unit(team, k, pos[0], pos[1], 12, 1, 1, 60, 4, 6)
        if k == 'Archer':
            return Unit(team, k, pos[0], pos[1], 9, 3, 1, 45, 2, 8)
        return Unit(team, k, pos[0], pos[1], 14, 1, 2, 50, 3, 7)

    def damage_value(self, attacker, defender):
        return max(0, attacker.atk - getattr(defender, 'armor', 0))