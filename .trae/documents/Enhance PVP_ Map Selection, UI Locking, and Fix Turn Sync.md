I will enhance the PVP mode with map selection, improved turn management, and fix the turn execution issue.

### 1. Host Map & Team Selection
I will update the "Create Room" flow to allow map and team selection before starting the server.
-   **Modify `GameController`**:
    -   When clicking "Host Game", show a submenu: "Random Map" or "Select Map".
    -   After map selection (or random), show "Select Team" (A or B).
    -   Only *after* team selection, start the server and enter `PVP_CONNECT` state.
-   **Network Protocol Update**:
    -   The `start` message broadcast by the server must now include the `seed` (for random maps) or the `map_data` (for custom maps) to ensure both clients load the *same* map.
    -   The `assign` message or initial negotiation needs to respect the host's team choice (e.g., if Host picked A, Client gets B).

### 2. Turn Commitment & UI Locking
I will implement a "Waiting" state to prevent actions after committing the turn.
-   **`PVPGameLoop`**: Add `self.waiting_for_server` check in `start_player_phase` or input handlers to block further actions.
-   **UI Update**:
    -   When `waiting_for_server` is True, render a "Waiting for Opponent..." overlay or label.
    -   Replace "End Turn" button with "Cancel Ready" (Undo Commit) button.
    -   **Logic**: If "Cancel Ready" is clicked, send a `cancel_turn` message to server. Server removes the player's actions from `turn_actions` and resets their ready status.

### 3. Fix Turn Execution & Synchronization
The "waiting for server" hang implies the server isn't broadcasting `turn_data` or the client isn't processing it correctly.
-   **Server Logic**: Verify `_check_turn_complete` logic. It should trigger when *both* `ready_for_next_turn` flags are True.
-   **Client Logic**: Ensure `PVPGameLoop.step()` correctly detects `turn_data`, applies it, and *then* advances the simulation.
-   **Debugging**: The issue might be that `step()` returns early when `waiting_for_server` is True, so it never processes the incoming `turn_data` message. I need to check the message queue *before* the return check.

### Implementation Plan
1.  **Map/Team Selection**:
    -   Update `src/pvp/config.py` with new buttons.
    -   Update `GameController` state machine for PVP setup flow.
    -   Update `Server` to accept and broadcast map config.
2.  **Turn Logic Fix**:
    -   Modify `PVPGameLoop.step` to process messages *even if* waiting.
    -   Debug server `_check_turn_complete`.
3.  **UI Locking & Undo**:
    -   Update `PVPGameLoop` to support `cancel_turn`.
    -   Update `Server` to handle `cancel_turn`.
    -   Update `GameController` to show "Waiting/Cancel" UI state.

I'll start by fixing the critical turn execution bug first, then add the UI/UX features.
