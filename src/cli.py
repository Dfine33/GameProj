import sys
import os
# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation.loop import SimulationLoop
from src.ai.policy import SimplePolicy
from src.renderer.char import CharRenderer

def main():
    loop = SimulationLoop(SimplePolicy(), CharRenderer())
    loop.run()

if __name__ == '__main__':
    main()