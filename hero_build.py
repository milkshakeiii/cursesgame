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

    def save_to_json(self):
        import json
        return json.dumps({
            "name": self.name,
            "form": str(self.form) if self.form else None,
            "background": str(self.background) if self.background else None,
            "levels": [(level.save_to_json()) for level in self.levels]
        }, indent=4)

class HeroLevel:
    def __init__(self, hero_class, level_number, modules):
        self.hero_class = hero_class
        self.level_number = level_number
        self.modules = modules
    def save_to_json(self):
        import json
        return json.dumps({
            "hero_class": str(self.hero_class) if self.hero_class else None,
            "level_number": self.level_number,
            "modules": [(module.save_to_json()) for module in self.modules]
        }, indent=4)