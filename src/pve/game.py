from simulation.loop import SimulationLoop
from ai.unit_policies import CompositePolicy

def start_pve_game(renderer, initial_state=None):
    """
    Initialize and return a SimulationLoop for PVE mode.
    Sets await_human=True to enable human interaction.
    """
    loop = SimulationLoop(CompositePolicy(), renderer, initial_state=initial_state)
    loop.await_human = True
    return loop
