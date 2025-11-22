from utils.common import hex_distance

class Action:
    def __init__(self, kind, target=None):
        self.kind = kind
        self.target = target

class DecisionPolicy:
    def decide(self, unit, gamestate):
        raise NotImplementedError

class SimplePolicy(DecisionPolicy):
    def decide(self, unit, gamestate):
        visible = []
        for e in gamestate.units:
            if e.team != unit.team and hex_distance(unit.pos(), e.pos()) <= unit.vision:
                visible.append(e)
        for b in [gamestate.base_a, gamestate.base_b]:
            if b.team != unit.team and hex_distance(unit.pos(), b.pos()) <= unit.vision:
                visible.append(b)
        target = None
        min_d = 10**9
        for v in visible:
            d = hex_distance(unit.pos(), v.pos())
            if d < min_d:
                min_d = d
                target = v
        if target and min_d <= unit.rng:
            return Action('attack', target)
        if target:
            return Action('move_towards', target.pos())
        return Action('wander')

class TwoPhasePolicy(DecisionPolicy):
    def __init__(self):
        self.goals = {}

    def decide(self, unit, gamestate):
        visible = []
        for e in gamestate.units:
            if e.team != unit.team and hex_distance(unit.pos(), e.pos()) <= unit.vision:
                visible.append(e)
        other_base = gamestate.base_b if unit.team == 'A' else gamestate.base_a
        if hex_distance(unit.pos(), other_base.pos()) <= unit.vision:
            gamestate.record_enemy_base(unit.team, other_base.pos())
            visible.append(other_base)
        tgt = None
        min_d = 10**9
        for v in visible:
            d = hex_distance(unit.pos(), v.pos())
            if d < min_d:
                min_d = d
                tgt = v
        if tgt and min_d <= unit.rng:
            return Action('attack', tgt)
        known = gamestate.known_enemy_base.get(unit.team)
        if known:
            return Action('move_towards', known)
        gid = id(unit)
        g = self.goals.get(gid)
        if not g or hex_distance(unit.pos(), g) <= 0:
            home = gamestate.base_a if unit.team == 'A' else gamestate.base_b
            candidates = []
            for y in range(gamestate.map.height):
                for x in range(gamestate.map.width):
                    if gamestate.map.can_walk(x, y):
                        d = hex_distance(home.pos(), (x, y))
                        candidates.append((d, (x, y)))
            candidates.sort(reverse=True)
            self.goals[gid] = candidates[0][1] if candidates else home.pos()
            g = self.goals[gid]
        return Action('move_towards', g)