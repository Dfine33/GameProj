I will implement the PVP (Player vs Player) mode with network connectivity.

### 1. Network Module Implementation
I'll create a simple client-server architecture using Python's `socket` module.
-   **`src/network/server.py`**: A server that manages the game state, receives actions from both clients, and broadcasts updates.
-   **`src/network/client.py`**: A client that connects to the server, sends local player actions, and receives the updated game state.
-   **Protocol**: JSON-based messages for simplicity (e.g., `{"type": "action", "data": ...}`, `{"type": "state_update", "data": ...}`).

### 2. PVP Game Loop Adaptation
I'll create a `PVPGameLoop` (or extend `SimulationLoop`) that:
-   **Overrides `step()`**: Instead of executing logic locally immediately, it sends collected actions to the server (or if host, executes them).
-   **Synchronization**: Waits for the server to confirm the turn processing before advancing the tick.
-   **Player Assignment**: One client is 'A' (Host), the other is 'B' (Client).

### 3. UI Integration
-   **`src/pvp/config.py`**: Define PVP menu buttons (Host Game, Join Game, IP Input).
-   **`src/pvp/game.py`**: Logic to initialize the PVP session.
-   **`src/controllers/game_controller.py`**:
    -   Add `MENU_PVP` state.
    -   Handle "Host" (start server thread + client) and "Join" (start client) actions.
    -   Add a simple input box for IP address when joining.

### 4. Implementation Steps
1.  **Create Directories**: Ensure `src/pvp` exists.
2.  **Network Logic**: Implement `Server` and `Client` classes in `src/network`.
3.  **PVP Logic**: Create `src/pvp/game.py` and `src/pvp/config.py`.
4.  **Controller Update**: Modify `GameController` to integrate PVP menus and game loop.
5.  **Testing**: Verify connection and basic turn syncing locally.

### Technical Detail: Lockstep Simulation
To keep it simple and consistent with the existing "turn-based/step" nature:
-   Both players plan their moves (recruit, move, attack) locally.
-   When both click "End Turn", actions are sent to the server.
-   Server aggregates actions, runs the `step()` logic (resolution), and sends back the new state (or just the actions for deterministic replay, but sending state is safer for now).
-   Clients update their local state.

I will start by creating the PVP module structure and network basics.
