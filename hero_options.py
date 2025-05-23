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