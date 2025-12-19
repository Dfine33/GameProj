from core.balance import UNIT_COSTS
import random

class ISpawnStrategy:
    def choose_units(self, points, team, state):
        raise NotImplementedError

class RandomSpawnStrategy(ISpawnStrategy):
    def choose_units(self, points, team, state):
        kinds = []
        options = list(UNIT_COSTS.items())
        while points >= min(UNIT_COSTS.values()):
            k, c = random.choice(options)
            if c <= points:
                kinds.append(k)
                points -= c
            else:
                # 尝试寻找可用的更便宜单位
                cheaper = [kk for kk, cc in options if cc <= points]
                if not cheaper:
                    break
                k = random.choice(cheaper)
                kinds.append(k)
                points -= UNIT_COSTS[k]
        return kinds
