import sys
from enum import Enum


if __name__ == "__main__":
    # test
    if len(sys.argv) != 2:
        print("Usage: python builder.py <number>")
        sys.exit(1)
    try:
        number = int(sys.argv[1])
    except ValueError:
        print("Please provide a valid integer.")
        sys.exit(1)
    print(number * 2)

class ActionType(Enum):
    NONE = 0
    DIRECT_ACTION = 1
    INDIRECT_ACTION = 2
    CHANNEL = 3

class Action:
    def __init__(self, action_type, actor, opponent):
        self.action_type = action_type
        self.actor = actor
        self.opponent = opponent
        self.triggers = []

class Battle:
    def __init__(self, hero1, hero2):
        self.hero1 = hero1
        self.hero2 = hero2
        self.ply = 0

    def do_turn(self, actor, opponent, action):
        self.ply += 1

        action = Action(action, actor, opponent)

        if action == ActionType.DIRECT_ACTION:
            self.direct_action(actor, opponent, action)
        elif action == ActionType.INDIRECT_ACTION:
            self.indirect_action(actor, opponent, action)
        elif action == ActionType.CHANNEL:
            self.channel(actor, opponent, action)
        else:
            raise ValueError("Invalid action type")

    def direct_action(self, actor, opponent, action):
        opponent.on_opponent_direct_action(actor, action)
        actor.on_direct_action(opponent, action)

    def indirect_action(self, actor, opponent, action):
        opponent.on_opponent_indirect_action(actor, action)
        actor.on_indirect_action(opponent, action)

    def channel(self, actor, opponent, action):
        opponent.on_opponent_channel(actor, action)
        actor.on_channel(opponent, action)

