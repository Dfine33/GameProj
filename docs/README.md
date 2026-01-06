# RTS Simulation Game

This is a Real-Time Strategy (RTS) simulation game built with Python and Pygame. It features both Computer vs Computer (EVE) and Player vs Computer (PVE) modes, along with a map editor and various simulation tools.

## Project Structure

The project follows a modular structure:

- `src/`: Core source code
  - `main.py`: Main game entry point
  - `map_editor.py`: Map editor entry point
  - `eve/`: EVE mode specific logic and configuration
  - `pve/`: PVE mode specific logic and configuration
  - `core/`: Core game state and logic
  - `simulation/`: Game loop and simulation engine
  - `renderer/`: Graphics rendering modules
  - `ai/`: AI policies and logic
  - `controllers/`: Input handling and game control
- `docs/`: Documentation files
- `tests/`: Unit tests
- `config/`: Configuration files

## Features

### EVE (Environment vs Environment / AI vs AI)
In this mode, two AI teams battle against each other.
- **Random Maps**: Generate random battlefields.
- **Custom Maps**: Load maps created with the Map Editor.
- **Observation**: Watch the AI strategies unfold.

### PVE (Player vs Environment)
In this mode, you play against an AI opponent.
- **Team Selection**: Choose to play as Red Team (A) or Blue Team (B).
- **Fog of War**: You can only see what your units see.
- **Controls**:
  - `Left Click`: Select unit
  - `Right Click`: Move/Attack
  - `Space`: Pause/Resume
  - `Arrow Keys`: Move camera

## Setup & Installation

1. **Prerequisites**:
   - Python 3.8+
   - Pygame (`pip install pygame`)

2. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd GameProj
   ```

3. **Install dependencies**:
   ```bash
   pip install pygame
   ```

## Running the Game

### Main Game
To start the game GUI:
```bash
python src/main.py
```

### Map Editor
To create custom maps:
```bash
python src/map_editor.py
```

### CLI Simulation
To run a headless simulation:
```bash
python src/cli.py
```

### Running Tests
To run the unit tests:
```bash
python -m unittest discover tests
```

## Documentation
- [Computer Strategy Overview](docs/computer_strategy.md)
- [Unit Logic](docs/unit_logic.md)

## License
[License Information]
