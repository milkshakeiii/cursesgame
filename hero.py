class Hero:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.tags = set()
        self.resources = {}
        self.modules = []

class HeroModule:
    def __init__(self, name):
        self.name = name
        self.tags
        self.prerequisites
        self.triggers
        self.conditions
        self.costs
        self.effects

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

class HeroClass:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    def __str__(self):
        return f"Hero Class: {self.name} - {self.description}"

class HeroLevel:
    def __init__(self, level, description):
        self.level = level
        self.description = description
    def __str__(self):
        return f"Hero Level: {self.level} - {self.description}"

class HeroBackground:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    def __str__(self):
        return f"Hero Background: {self.name} - {self.description}"

class HeroForm:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    def __str__(self):
        return f"Hero Form: {self.name} - {self.description}"