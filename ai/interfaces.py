class IDecisionModel:
    def decide(self, unit, game_state):
        raise NotImplementedError

from ai.policy import SimplePolicy

class RandomDecisionModel(SimplePolicy):
    pass