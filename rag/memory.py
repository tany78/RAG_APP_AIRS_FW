from typing import List, Dict

class ChatMemory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add(self, user: str, bot: str):
        self.history.append({"user": user, "bot": bot})

    def get(self) -> List[Dict[str, str]]:
        return self.history

    def reset(self):
        self.history = []
