class Effect:
    def apply(self, actor, opponent, module, action):
        # Apply the effect to the given hero
        raise NotImplementedError("Use an effect subclass")