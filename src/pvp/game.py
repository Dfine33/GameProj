from src.simulation.loop import SimulationLoop
from src.ai.unit_policies import CompositePolicy
from src.ai.policy import Action
from src.core.state import GameState

class PVPGameLoop(SimulationLoop):
    def __init__(self, renderer, client, initial_state=None):
        super().__init__(CompositePolicy(), renderer, initial_state)
        self.client = client
        self.await_human = True # PVP is always waiting for human input locally
        self.waiting_for_server = False # Block 'next turn' until server confirms
        self.error_message = None # Store critical errors (Disconnect/Desync)

    def start_pvp_phase(self):
        # Initialize local player context
        if self.client.team:
            self.player_team = self.client.team
            self.start_player_phase()
            print(f"DEBUG: Started PVP phase for team {self.player_team}")

    def cancel_turn(self):
        """
        Called when player clicks 'Cancel Ready'
        Sends cancel signal to server
        """
        if not self.waiting_for_server:
            return

        payload = {
            'type': 'cancel_turn'
        }
        self.client.send_actions([payload]) # Using send_actions wrapper for convenience, but structure is slightly different
        # Actually client.send_actions wraps in {type: actions, data: [...]}.
        # We need a raw send or update send_actions.
        # Let's use client._send directly or add a method.
        # Accessing private _send is ok for now or better add send_cancel in client.
        self.client._send(payload)
        
        self.waiting_for_server = False
        print("Turn cancelled")

    def step(self, print_every=10):
        # Check for network messages
        msgs = self.client.get_messages()
        if self.waiting_for_server and len(msgs) > 0:
            print(f"DEBUG: PVPGameLoop step found {len(msgs)} messages while waiting")

        for msg in msgs:
            if msg['type'] == 'start':
                print("PVP Game Started!")
                self.start_pvp_phase()
                # Ensure local phase is ready immediately
                self.await_human = True
                self.waiting_for_server = False
            elif msg['type'] == 'disconnect':
                print("Opponent disconnected")
                self.error_message = "对手已断开连接"
                # Handle game over or pause?
            elif msg['type'] == 'turn_data':
                print(f"DEBUG: Received turn_data for Tick {self.state.tick}, applying...")
                try:
                    self._apply_server_turn(msg['actions'])
                    self.waiting_for_server = False
                    print(f"DEBUG: Turn applied. New Tick: {self.state.tick}")
                except Exception as e:
                    print(f"CRITICAL ERROR applying turn: {e}")
                    import traceback
                    traceback.print_exc()
            elif msg['type'] == 'desync':
                print(f"CRITICAL: Game State Desync Detected! Server Checksums: {msg.get('checksums')}")
                self.error_message = "发生同步错误 (Desync)!"
                
        # If we are waiting for server (after ending turn), do NOT run local step logic
        # But return True to keep loop alive for polling
        if self.waiting_for_server:
            # Optional: Periodic log if waiting too long
            # if time.time() % 5 < 0.1: print("Waiting for server...") 
            return True
            
        # Standard step logic is skipped here because PVP is strictly lockstep
        # We only advance when we receive 'turn_data' from server
        return self.state.base_a.hp > 0 and self.state.base_b.hp > 0

    def commit_turn(self):
        """
        Called when player clicks 'End Turn'
        Sends local actions to server and enters waiting state
        """
        if self.waiting_for_server:
            return

        # Serialize local actions
        actions_payload = []
        
        # 1. Recruitments
        for rec in self.player_recruits:
            actions_payload.append({
                'kind': 'recruit',
                'unit_type': rec['kind'],
                'pos': rec['pos']
            })
            
        # 2. Unit commands
        for u, act in self.player_actions.items():
            # Only send non-idle actions
            if act.kind != 'idle':
                # Serialize action
                act_data = {'kind': act.kind}
                if hasattr(act.target, 'pos'): # Unit target
                     # We need a way to ID units across network. 
                     # For MVP, we might rely on coordinate matching or assume deterministic ID generation if careful.
                     # But IDs are safer. GameState needs to ensure IDs are consistent.
                     # For now, let's use target ID if available, or pos if it's a move_path
                     act_data['target_id'] = id(act.target) # Python ID won't work across net!
                     # FIXME: Need stable IDs for units.
                     # Fallback: For attacks, send target grid pos.
                     tx, ty = act.target.pos()
                     act_data['target_pos'] = (tx, ty)
                elif isinstance(act.target, tuple): # Coord target
                    act_data['target_pos'] = act.target
                elif isinstance(act.target, list): # Path target
                    act_data['target_path'] = act.target
                
                # Identify which unit is acting by its position (assuming unique per tile) or ID
                ux, uy = u.pos()
                actions_payload.append({
                    'kind': 'command',
                    'unit_pos': (ux, uy),
                    'action': act_data
                })

        # Send to server
        # Calculate checksum of current state (before applying this turn's actions, 
        # but wait, this turn's actions are applied next turn? 
        # Lockstep: 
        # Turn N starts. 
        # Players plan actions. 
        # Commit (send actions + checksum of State at start of Turn N or end of Turn N-1).
        # Server gathers. 
        # Server sends Turn N actions.
        # Clients apply actions -> State becomes Turn N+1.
        # So we should send checksum of the state *as it is right now* (Turn N start).
        checksum = self.state.get_checksum()
        self.client.send_actions(actions_payload, checksum=checksum)
        self.waiting_for_server = True
        print(f"Turn committed (Tick {self.state.tick}, Checksum {checksum[:8]}), waiting for server...")

    def _apply_server_turn(self, all_actions):
        """
        Apply actions received from server for both teams, then advance tick
        """
        # 1. Reset local state for resolution
        # Clear local planned actions as they are now being executed authoritatively
        self.player_recruits = []
        self.player_actions = {}
        
        # 2. Apply Spawn/Recruit Actions
        # We need to process both A and B
        for team in ['A', 'B']:
            team_acts = all_actions.get(team, [])
            for act in team_acts:
                if act['kind'] == 'recruit':
                    # Server says recruit at pos
                    pos = tuple(act['pos'])
                    kind = act['unit_type']
                    # Verify validity simply (or trust server/peer)
                    if self.state.map.can_walk(*pos) and pos not in self.state.occupied:
                        nu = self.state.spawn_unit(team, pos, kind)
                        self.state.add_unit(nu)
                        print(f"DEBUG: Spawned {kind} for {team} at {pos}")
        
        # 3. Apply Unit Commands
        # We need to map coordinate/ID back to local unit objects
        # Create a map of pos -> unit for quick lookup
        # 注意：这里需要先更新 occupied，因为招募可能新增了单位
        self.state.update_occupied()
        pos_to_unit = {u.pos(): u for u in self.state.units}
        
        collected_actions = []
        
        for team in ['A', 'B']:
            team_acts = all_actions.get(team, [])
            for act in team_acts:
                if act['kind'] == 'command':
                    u_pos = tuple(act['unit_pos'])
                    unit = pos_to_unit.get(u_pos)
                    if unit and unit.team == team:
                        # Decode Action
                        act_data = act['action']
                        kind = act_data['kind']
                        target = None
                        
                        if 'target_pos' in act_data:
                            tx, ty = act_data['target_pos']
                            # If attack, find unit at target
                            if kind == 'attack':
                                target = pos_to_unit.get((tx, ty))
                                # Also check bases
                                if not target:
                                    if (tx, ty) == self.state.base_a.pos():
                                        target = self.state.base_a
                                    elif (tx, ty) == self.state.base_b.pos():
                                        target = self.state.base_b
                            else:
                                target = (tx, ty)
                        elif 'target_path' in act_data:
                            target = [tuple(p) for p in act_data['target_path']]
                        
                        if kind == 'attack' and not target:
                            # Target gone or invalid
                            action_obj = Action('idle', None)
                        else:
                            # 重新构建Action对象，特别是move_path需要确保路径被正确识别
                            # 如果是move_path，target应该是一个列表
                            if kind == 'move_path' and isinstance(target, list):
                                action_obj = Action(kind, target)
                            else:
                                action_obj = Action(kind, target)
                        
                        collected_actions.append((unit, action_obj))
        
        # 4. Run Simulation Step Resolution
        # We reuse the logic from SimulationLoop but applied with these specific actions
        # 注意：resolve_movements 依赖于 _vis_cache 和 _is_known_walkable
        # 因此在结算前必须更新 _vis_cache
        self._vis_cache['A'] = self._compute_visibility('A')
        self._vis_cache['B'] = self._compute_visibility('B')
        
        self.resolve_attacks(collected_actions)
        self.resolve_movements(collected_actions)
        
        # 5. Advance State
        self.state.tick += 1
        self.state.update_occupied()
        
        # 6. Prepare next local turn
        self.start_player_phase() # Re-calc points, etc.
