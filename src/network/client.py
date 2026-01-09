import socket
import threading
import json
import queue

class GameClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.team = None
        self.msg_queue = queue.Queue()
        self.running = False

    def connect(self, host, port=5000):
        try:
            self.sock.connect((host, port))
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connected = True
            self.running = True
            
            # Start receive thread
            self.recv_thread = threading.Thread(target=self._receive_loop)
            self.recv_thread.daemon = True
            self.recv_thread.start()
            print(f"Client connected to {host}:{port}, receive thread started")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _receive_loop(self):
        print("DEBUG: Receive loop running")
        buffer = b""
        try:
            while self.running:
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        print("Connection closed by server")
                        break
                    
                    print(f"DEBUG: Recv {len(data)} bytes")
                    buffer += data
                    
                    # Handle potential sticky packets or split packets
                    while b'\n' in buffer:
                        line_bytes, rest = buffer.split(b'\n', 1)
                        buffer = rest
                        if line_bytes.strip():
                            try:
                                line = line_bytes.decode('utf-8')
                                msg = json.loads(line)
                                print(f"DEBUG: Client received msg type: {msg.get('type')}")
                                self._handle_message(msg)
                            except UnicodeDecodeError as e:
                                print(f"Decode error: {e}")
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e} for line: {line_bytes}")
                except socket.error as e:
                    print(f"Socket error in receive loop: {e}")
                    break
                except Exception as e:
                    print(f"Receive loop exception: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        finally:
            self.connected = False
            print("DEBUG: Client receive loop exited")

    def _handle_message(self, msg):
        mtype = msg.get('type')
        if mtype == 'assign':
            self.team = msg.get('team')
            print(f"Assigned team: {self.team}")
        
        # Enqueue all messages for the game loop to process safely
        self.msg_queue.put(msg)

    def send_actions(self, actions, checksum=None):
        """
        Send local actions to server
        actions: list of action dicts
        checksum: optional state checksum for desync detection
        """
        if not self.connected:
            print("WARNING: send_actions called but client not connected")
            return
        
        if hasattr(self, 'recv_thread') and not self.recv_thread.is_alive():
             print("WARNING: Receive thread is DEAD but connected is True!")
        
        payload = {
            'type': 'actions',
            'data': actions
        }
        if checksum:
            payload['checksum'] = checksum
            
        self._send(payload)

    def _send(self, msg):
        try:
            # Append newline as delimiter
            data = (json.dumps(msg) + '\n').encode('utf-8')
            self.sock.sendall(data)
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False

    def close(self):
        self.running = False
        self.sock.close()

    def get_messages(self):
        msgs = []
        while not self.msg_queue.empty():
            try:
                msgs.append(self.msg_queue.get_nowait())
            except queue.Empty:
                break
        return msgs
