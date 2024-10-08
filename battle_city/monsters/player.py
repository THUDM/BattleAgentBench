from battle_city.monsters.tank import Tank


class Player(Tank):
    player_id = 0
    score = 0
    ready = False
    connection = None
    is_game_over = False
    nick = None  # type: str
    had_action = False
    target = -1
    health = 5
    action_number = 0
    
    def __init__(self, player_id, x, y):
        super().__init__(x, y)
        # if player_id not in range(6):
        #     raise ValueError('player_id')
        self.player_id = player_id

    def set_connection(self, connection):
        self.connection = connection

    def set_had_action(self):
        self.had_action = True

    def set_game_over(self):
        self.is_game_over = True

    def set_nick(self, nick: str):
        self.nick = nick
        self.ready = True

