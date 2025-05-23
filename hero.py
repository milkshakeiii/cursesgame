class Hero:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.tags = set()
        self.resources = {}
        self.modules = []