class HeroForm:
    def __init__(self, name, hero_tags, modules, description):
        self.name = name
        self.hero_tags = hero_tags
        self.modules = modules
        self.description = description
    def __str__(self):
        return f"Hero Form: {self.name} - {self.description}"

forms = [
    HeroForm("Human", {"human"}, [], "A native species of highly encephalized ape."),
]