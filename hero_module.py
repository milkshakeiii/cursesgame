class HeroModule:
    def __init__(self, name):
        self.name = name
        self.choices = [] # (text, value)
        self.tags = set()
        self.prerequisites = []
        self.triggers = []
        self.conditions = []
        self.costs = {}
        self.effects = []

    def save_to_json(self):
        import json
        return json.dumps({
            "name": self.name,
            "choices": self.choices,
            "tags": list(self.tags),
            "prerequisites": [prereq.save_to_json() for prereq in self.prerequisites],
            "triggers": [str(trigger) for trigger in self.triggers],
            "conditions": [str(condition) for condition in self.conditions],
            "costs": {str(key): value for key, value in self.costs.items()},
            "effects": [str(effect) for effect in self.effects]
        }, indent=4)