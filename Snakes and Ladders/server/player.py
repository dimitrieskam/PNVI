import json
import os

PROFILE_FILE = "player.json"

class Player:
    def __init__(self, username, avatar):
        self.username = username
        self.avatar = avatar
        self.wins = 0
        self.losses = 0
        self.fastest_win = None

    def record_win(self, moves):
        self.wins += 1
        if self.fastest_win is None or moves < self.fastest_win:
            self.fastest_win = moves

    def record_loss(self):
        self.losses += 1

    def save(self):
        data = {
            "username": self.username,
            "avatar": self.avatar,
            "wins": self.wins,
            "losses": self.losses,
            "fastest_win": self.fastest_win
        }
        with open(PROFILE_FILE, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load():
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
            p = Player(data["username"], data["avatar"])
            p.wins = data["wins"]
            p.losses = data["losses"]
            p.fastest_win = data["fastest_win"]
            return p
        return None
