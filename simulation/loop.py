import random
import sys
import threading
import time
from core.state import GameState
from utils.common import hex_neighbors, hex_distance

class SimulationLoop:
    def __init__(self, policy, renderer=None):
        self.policy = policy
        self.renderer = renderer
        self.state = GameState()
        self.lock = threading.Lock()

    def step_towards(self, unit, dest):
        ux, uy = unit.pos()
        nbrs = hex_neighbors(ux, uy)
        random.shuffle(nbrs)
        best = None
        best_d = 10**9
        for nx, ny in nbrs:
            if self.state.map.can_walk(nx, ny) and (nx, ny) not in self.state.occupied:
                d = hex_distance((nx,ny), dest)
                if d < best_d:
                    best_d = d
                    best = (nx, ny)
        if best is not None:
            unit.x, unit.y = best
            return True
        return False

    def wander(self, unit):
        nbrs = hex_neighbors(unit.x, unit.y)
        random.shuffle(nbrs)
        for nx, ny in nbrs:
            if self.state.map.can_walk(nx, ny) and (nx, ny) not in self.state.occupied:
                unit.x = nx
                unit.y = ny
                return True
        return False

    def spawn_from_base(self, base):
        if base.spawn_cooldown > 0:
            base.spawn_cooldown -= 1
            return
        spots = [p for p in hex_neighbors(base.x, base.y) if self.state.map.in_bounds(p[0], p[1])]
        random.shuffle(spots)
        placed = False
        for sx, sy in spots:
            if self.state.map.can_walk(sx, sy) and (sx, sy) not in self.state.occupied:
                nu = self.state.spawn_unit(base.team, (sx, sy))
                self.state.add_unit(nu)
                base.spawn_cooldown = random.randint(2, 4)
                placed = True
                break
        if not placed:
            base.spawn_cooldown = 1

    def apply_action(self, unit, action):
        if action.kind == 'attack':
            target = action.target
            if hasattr(target, 'pos'):
                if hasattr(target, 'hp'):
                    if abs(unit.x - target.x) + abs(unit.y - target.y) <= unit.rng:
                        dmg = self.state.damage_value(unit, target)
                        target.hp -= dmg
                        if hasattr(target, 'kind') and target.hp <= 0:
                            self.state.remove_unit(target)
            else:
                return
        elif action.kind == 'move_towards':
            for _ in range(unit.spd):
                if self.step_towards(unit, action.target):
                    self.state.occupied.add(unit.pos())
        elif action.kind == 'wander':
            for _ in range(unit.spd):
                if self.wander(unit):
                    self.state.occupied.add(unit.pos())

    def step(self, print_every=10):
        with self.lock:
            self.state.update_occupied()
            self.spawn_from_base(self.state.base_a)
            self.spawn_from_base(self.state.base_b)
            for u in list(self.state.units):
                act = self.policy.decide(u, self.state)
                self.apply_action(u, act)
            if self.renderer is not None and self.state.tick % print_every == 0:
                out = self.renderer.render(self.state, self.state.tick)
                if out:
                    print(out)
                    sys.stdout.flush()
            self.state.tick += 1
            cont = self.state.base_a.hp > 0 and self.state.base_b.hp > 0
            return cont

    def run(self, max_ticks=1000, print_every=10):
        random.seed()
        while self.state.tick < max_ticks:
            cont = self.step(print_every)
            if not cont:
                break
        if self.renderer is not None:
            out = self.renderer.render(self.state, self.state.tick)
            if out:
                print(out)
        if self.state.base_a.hp <= 0 and self.state.base_b.hp <= 0:
            print('平局')
            if self.renderer is not None:
                sys.stdout.flush()
        elif self.state.base_a.hp <= 0:
            print('胜利方：乙方')
            print('胜利方法：攻破对方基地')
            if self.renderer is not None:
                sys.stdout.flush()
        elif self.state.base_b.hp <= 0:
            print('胜利方：甲方')
            print('胜利方法：攻破对方基地')
            if self.renderer is not None:
                sys.stdout.flush()
        else:
            print('未分胜负')
            if self.renderer is not None:
                sys.stdout.flush()