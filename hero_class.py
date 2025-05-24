class HeroClass:
    def __init__(self, name, hero_tags, modules, description):
        self.name = name
        self.hero_tags = hero_tags
        self.modules = modules
        self.description = description
    def __str__(self):
        return f"Hero Class: {self.name} - {self.description}"

classes = [
    HeroClass("Warrior", {"warrior"}, [], "A strong and brave fighter."),
]