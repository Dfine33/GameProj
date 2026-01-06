class INetworkSession:
    def send_state(self, game_state):
        raise NotImplementedError

    def receive_input(self):
        raise NotImplementedError

    def sync(self):
        raise NotImplementedError