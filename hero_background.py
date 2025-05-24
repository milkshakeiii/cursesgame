class HeroBackground:
    def __init__(self, name, hero_tags, modules, description):
        self.name = name
        self.hero_tags = hero_tags
        self.modules = modules
        self.description = description
    def __str__(self):
        return f"Hero Background: {self.name} - {self.description}"

backgrounds = [
    HeroBackground("Adventurer", {"adventurer"}, [], "An adventurer with a thirst for exploration."),
]