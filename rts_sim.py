from simulation.loop import SimulationLoop
from ai.policy import SimplePolicy
from renderer.char import CharRenderer

def main():
    loop = SimulationLoop(SimplePolicy(), CharRenderer())
    loop.run()

if __name__ == '__main__':
    main()