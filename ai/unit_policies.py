from ai.policy import DecisionPolicy, Action
from utils.common import hex_distance

class UnitPolicy(DecisionPolicy):
    pass

class ScoutPolicy(UnitPolicy):
    def decide(self, unit, gamestate):
        other_base = gamestate.base_b if unit.team == 'A' else gamestate.base_a
        if hex_distance(unit.pos(), other_base.pos()) <= unit.vision:
            gamestate.record_enemy_base(unit.team, other_base.pos())
        known = gamestate.known_enemy_base.get(unit.team)
        if known:
            if hex_distance(unit.pos(), known) <= unit.rng:
                return Action('attack', other_base)
            return Action('move_towards', known)
        # 探索更远点
        home = gamestate.base_a if unit.team == 'A' else gamestate.base_b
        best = None; best_d = -1
        for y in range(gamestate.map.height):
            for x in range(gamestate.map.width):
                if gamestate.map.can_walk(x, y):
                    d = hex_distance(home.pos(), (x, y))
                    if d > best_d:
                        best_d = d; best = (x, y)
        return Action('move_towards', best or unit.pos())

class InfantryPolicy(UnitPolicy):
    def decide(self, unit, gamestate):
        # 最近目标优先
        tgt = None; md = 10**9
        for e in gamestate.units + [gamestate.base_a, gamestate.base_b]:
            if getattr(e, 'team', unit.team) != unit.team:
                d = hex_distance(unit.pos(), e.pos())
                if d < md:
                    md = d; tgt = e
        if tgt and md <= unit.rng:
            return Action('attack', tgt)
        if tgt:
            return Action('move_towards', tgt.pos())
        return Action('wander')

class ArcherPolicy(UnitPolicy):
    def decide(self, unit, gamestate):
        tgt = None; md = 10**9
        for e in gamestate.units + [gamestate.base_a, gamestate.base_b]:
            if getattr(e, 'team', unit.team) != unit.team:
                d = hex_distance(unit.pos(), e.pos())
                if d < md:
                    md = d; tgt = e
        if tgt and md <= unit.rng:
            return Action('attack', tgt)
        if tgt:
            # 保持距离，向射程边缘移动
            return Action('move_towards', tgt.pos())
        return Action('wander')

class CompositePolicy(DecisionPolicy):
    def __init__(self):
        self._policies = {
            'Scout': ScoutPolicy(),
            'Infantry': InfantryPolicy(),
            'Archer': ArcherPolicy(),
        }
    def decide(self, unit, gamestate):
        p = self._policies.get(unit.kind)
        if p:
            return p.decide(unit, gamestate)
        return InfantryPolicy().decide(unit, gamestate)
