import socket
import threading
import json
import time

class GameServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {conn: team}
        self.team_map = {} # {team: conn}
        self.lock = threading.Lock()
        self.running = False
        self.game_started = False
        
        self.game_config = {'mode': 'random'}
        self.host_team = 'A'
        
        # Store pending actions for the current turn
        # {team: [action_dicts]}
        self.turn_actions = {'A': [], 'B': []}
        self.turn_checksums = {'A': None, 'B': None}
        self.ready_for_next_turn = {'A': False, 'B': False}

    def set_game_config(self, config, host_team):
        self.game_config = config
        self.host_team = host_team

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(2)
            self.running = True
            print(f"Server started on {self.host}:{self.port}")
            
            # Start accepting connections in a separate thread
            accept_thread = threading.Thread(target=self._accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            print(f"Server start error: {e}")
            self.running = False

    def _accept_clients(self):
        # Determine team assignment order based on host_team
        # If host is A, first client (host) gets A, second gets B
        # If host is B, first client (host) gets B, second gets A
        # Wait, self._accept_clients runs in a loop.
        # The first connection is typically the host if started immediately after bind.
        # But to be safe, we can just assign based on order.
        # Simple Logic: First connection gets self.host_team, second gets the other.
        
        teams_order = [self.host_team, 'B' if self.host_team == 'A' else 'A']
        
        while self.running and len(self.clients) < 2:
            try:
                conn, addr = self.server_socket.accept()
                with self.lock:
                    if len(self.clients) >= 2:
                        conn.close()
                        continue
                    
                    team = teams_order[len(self.clients)]
                    self.clients[conn] = team
                    self.team_map[team] = conn
                    print(f"Client connected from {addr}, assigned team {team}")
                    
                    # Send assignment
                    self._send(conn, {'type': 'assign', 'team': team})
                    
                    # Start handler
                    handler = threading.Thread(target=self._handle_client, args=(conn, team))
                    handler.daemon = True
                    handler.start()
                    
                    if len(self.clients) == 2:
                        self.game_started = True
                        # Use a slight delay or ensure the second client is ready to receive
                        time.sleep(0.1) 
                        # Broadcast start with map config
                        self._broadcast({'type': 'start', 'msg': 'Game Started', 'config': self.game_config})
                        print("Broadcasted start message")
            except Exception as e:
                print(f"Accept error: {e}")

    def _handle_client(self, conn, team):
        buffer = b""
        while self.running:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                
                buffer += data
                while b'\n' in buffer:
                    line_bytes, rest = buffer.split(b'\n', 1)
                    buffer = rest
                    if line_bytes.strip():
                        try:
                            line = line_bytes.decode('utf-8')
                            msg = json.loads(line)
                            self._process_message(team, msg)
                        except UnicodeDecodeError:
                            print(f"Decode error from team {team}")
                        except json.JSONDecodeError:
                            print(f"JSON decode error from team {team}")
            except Exception as e:
                print(f"Client {team} error: {e}")
                break
        
        with self.lock:
            if conn in self.clients:
                del self.clients[conn]
                del self.team_map[team]
                self.game_started = False
                self._broadcast({'type': 'disconnect', 'team': team})

    def _process_message(self, team, msg):
        mtype = msg.get('type')
        
        if mtype == 'actions':
            # Receive actions from a player for the current turn
            with self.lock:
                self.turn_actions[team] = msg.get('data', [])
                self.turn_checksums[team] = msg.get('checksum')
                self.ready_for_next_turn[team] = True
                self._check_turn_complete()
        elif mtype == 'cancel_turn':
            with self.lock:
                self.ready_for_next_turn[team] = False
                self.turn_actions[team] = []
                self.turn_checksums[team] = None
                print(f"Team {team} cancelled turn ready state")
                
    def _check_turn_complete(self):
        # If both players have sent their actions (or ready signal)
        if self.ready_for_next_turn['A'] and self.ready_for_next_turn['B']:
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            print(f"[{timestamp}] Both players ready. Verifying checksums...")
            
            # Verify checksums if available
            ca = self.turn_checksums.get('A')
            cb = self.turn_checksums.get('B')
            if ca and cb:
                if ca != cb:
                    print(f"[{timestamp}] CRITICAL: DESYNC DETECTED! A:{ca} != B:{cb}")
                    self._broadcast({
                        'type': 'desync',
                        'checksums': self.turn_checksums
                    })
                else:
                    print(f"[{timestamp}] Checksums match: {ca}")
            else:
                print(f"[{timestamp}] Warning: Missing checksums A:{ca} B:{cb}")
            
            # Broadcast all actions to both players
            # Clients will apply them locally to sync state
            payload = {
                'type': 'turn_data',
                'actions': {
                    'A': self.turn_actions['A'],
                    'B': self.turn_actions['B']
                },
                'timestamp': time.time()
            }
            print(f"[{timestamp}] Broadcasting turn_data to clients...")
            self._broadcast(payload)
            
            # Reset for next turn
            self.turn_actions = {'A': [], 'B': []}
            self.turn_checksums = {'A': None, 'B': None}
            self.ready_for_next_turn = {'A': False, 'B': False}

    def _send(self, conn, msg):
        try:
            json_str = json.dumps(msg)
            data = (json_str + '\n').encode('utf-8')
            # print(f"DEBUG: Server sending {len(data)} bytes to {self.clients.get(conn, 'Unknown')}")
            conn.sendall(data)
            return True
        except Exception as e:
            print(f"Send error to {self.clients.get(conn, 'Unknown')}: {e}")
            return False

    def _broadcast(self, msg):
        count = 0
        for conn in list(self.clients.keys()): # Use list to avoid runtime error if dict changes
            if self._send(conn, msg):
                count += 1
        print(f"Broadcasted to {count} clients")

    def stop(self):
        self.running = False
        self.server_socket.close()
