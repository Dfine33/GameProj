import unittest
import sys
import os

# Add src directory to path so that 'core', 'simulation' etc can be imported directly if needed
# AND add project root so 'src' package can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from simulation.loop import SimulationLoop
from ai.policy import SimplePolicy
from core.state import GameState

class TestSimulation(unittest.TestCase):
    def test_initialization(self):
        loop = SimulationLoop(SimplePolicy())
        self.assertIsNotNone(loop.state)
        self.assertIsInstance(loop.state, GameState)
        self.assertEqual(loop.state.tick, 0)

    def test_step(self):
        loop = SimulationLoop(SimplePolicy())
        initial_tick = loop.state.tick
        loop.step()
        self.assertEqual(loop.state.tick, initial_tick + 1)

    def test_game_over_condition(self):
        loop = SimulationLoop(SimplePolicy())
        loop.state.base_a.hp = 0
        cont = loop.step()
        self.assertFalse(cont)

if __name__ == '__main__':
    unittest.main()
