class HeroBuild:
    def __init__(self, name):
        self.name = name
        self.form
        self.background
        self.levels = []

    def tags(self):
        return set()

    def __str__(self):
        return f"Hero Build: {self.name}"

    def level(self):
        return len(self.levels)