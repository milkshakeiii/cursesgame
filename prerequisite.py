class Prerequisite:
    def check(self, hero_build):
        # Check if the prerequisite is met for the given hero_build
        raise NotImplementedError("Use a prerequisite subclass")

class HasTag(Prerequisite):
    def __init__(self, tag):
        self.tag = tag
    def check(self, hero_build):
        return self.tag in hero_build.tags()

class AtLeastLevel(Prerequisite):
    def __init__(self, level):
        self.level = level
    def check(self, hero_build):
        return hero_build.level >= self.level
