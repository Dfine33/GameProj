from simulation.loop import SimulationLoop
from ai.unit_policies import CompositePolicy

def start_eve_game(renderer, initial_state=None):
    """
    Initialize and return a SimulationLoop for EVE mode.
    """
    loop = SimulationLoop(CompositePolicy(), renderer, initial_state=initial_state)
    return loop
