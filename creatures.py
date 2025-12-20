"""Creature definitions registry based on GAME_ENTITIES.md."""

import copy
import random
from typing import Optional

from game_data import Attack, Creature


def _create_attack(
    attack_type: str,
    damage: int,
    range_min: Optional[int] = None,
    range_max: Optional[int] = None,
    abilities: Optional[list[str]] = None,
) -> Attack:
    """Helper to create an Attack with proper defaults."""
    return Attack(
        attack_type=attack_type,
        damage=damage,
        range_min=range_min,
        range_max=range_max,
        abilities=abilities or [],
    )


# Creature templates organized by biome and terrain
CREATURE_REGISTRY: dict[str, dict[str, dict[str, Creature]]] = {
    "forest": {
        "grass": {
            "Wolf": Creature(
                name="Wolf",
                symbol="w",
                color=(80, 90, 80),
                max_health=10,
                current_health=10,
                defense=2,
                dodge=1,
                resistance=2,
                conversion_efficacy=75,
                attacks=[_create_attack("melee", 4)],
                abilities=[],
                base_requirement=5,
                tier_bonuses=[
                    {"tier": 1, "battles": 5, "abilities": ["Pack Hunter"]},
                    {
                        "tier": 2,
                        "battles": 10,
                        "defense": 2,
                        "dodge": 2,
                        "resistance": 2,
                        "melee_damage": 4,
                        "max_health": 8,
                    },
                ],
            ),
        },
        "trees": {
            "Giant Spider": Creature(
                name="Giant Spider",
                symbol="s",
                color=(120, 120, 120),
                max_health=15,
                current_health=15,
                defense=1,
                dodge=3,
                resistance=2,
                conversion_efficacy=25,
                attacks=[_create_attack("ranged", 4, 1, 2, ["Weakening"])],
                abilities=[],
                base_requirement=10,
                tier_bonuses=[
                    {
                        "tier": 1,
                        "battles": 10,
                        "size": "2x2",
                        "glyphs": ["s", "s", "s", "s"],
                        "max_health": 15,
                        "defense": 2,
                        "dodge": 2,
                        "resistance": 3,
                        "conversion_efficacy": -15,
                        "ranged_damage": 6,
                    },
                ],
            ),
        },
        "bushes": {
            "Goblin Pikeman": Creature(
                name="Goblin Pikeman",
                symbol="p",
                color=(80, 120, 60),
                max_health=12,
                current_health=12,
                defense=3,
                dodge=1,
                resistance=1,
                conversion_efficacy=50,
                attacks=[_create_attack("melee", 5, abilities=["Piercing"])],
                abilities=[],
                base_requirement=6,
                tier_bonuses=[
                    {"tier": 1, "battles": 6, "defense": 1, "melee_damage": 2},
                    {"tier": 2, "battles": 12, "abilities": ["Shield Wall"]},
                ],
            ),
        },
        "hill": {
            "Centaur Shaman": Creature(
                name="Centaur Shaman",
                symbol="C",
                color=(140, 90, 60),
                max_health=15,
                current_health=15,
                defense=2,
                dodge=2,
                resistance=3,
                conversion_efficacy=40,
                attacks=[
                    _create_attack("melee", 4),
                    _create_attack("magic", 7),
                ],
                abilities=[],
                base_requirement=8,
                tier_bonuses=[
                    {
                        "tier": 1,
                        "battles": 8,
                        "defense": 1,
                        "dodge": 1,
                        "resistance": 1,
                        "melee_damage": 1,
                        "magic_damage": 1,
                    },
                ],
            ),
        },
    },
    "plains": {
        "short_grass": {
            "Eagle": Creature(
                name="Eagle",
                symbol="E",
                color=(200, 200, 180),
                max_health=8,
                current_health=8,
                defense=1,
                dodge=3,
                resistance=1,
                conversion_efficacy=45,
                attacks=[_create_attack("melee", 6)],
                abilities=["Haste", "Flying"],
                base_requirement=7,
                tier_bonuses=[
                    {
                        "tier": 1,
                        "battles": 7,
                        "new_attack": {"type": "ranged", "damage": 6, "range": "2-3"},
                        "abilities": ["Evasion 50%"],
                    },
                ],
            ),
        },
        "tall_grass": {
            "Lion": Creature(
                name="Lion",
                symbol="L",
                color=(200, 170, 80),
                max_health=12,
                current_health=12,
                defense=3,
                dodge=1,
                resistance=2,
                conversion_efficacy=70,
                attacks=[_create_attack("melee", 5)],
                abilities=[],
                base_requirement=5,
                tier_bonuses=[
                    {"tier": 1, "battles": 5, "abilities": ["Protector"]},
                    {
                        "tier": 2,
                        "battles": 10,
                        "defense": 2,
                        "dodge": 2,
                        "resistance": 2,
                        "melee_damage": 4,
                        "max_health": 8,
                    },
                    {"tier": 3, "battles": 15, "abilities": ["Guardian"]},
                ],
            ),
            "Scorpion": Creature(
                name="Scorpion",
                symbol="S",
                color=(140, 110, 60),
                max_health=11,
                current_health=11,
                defense=2,
                dodge=2,
                resistance=1,
                conversion_efficacy=20,
                attacks=[_create_attack("ranged", 4, 1, 2, ["Blinding"])],
                abilities=[],
                base_requirement=9,
                tier_bonuses=[
                    {"tier": 1, "battles": 9, "attack_abilities": {"ranged": ["Silencing"]}},
                ],
            ),
        },
    },
    "snow": {
        "snow": {
            "Yeti": Creature(
                name="Yeti",
                symbol="Y",
                color=(220, 230, 240),
                size="2x2",
                glyphs=["Y", "Y", "Y", "Y"],
                max_health=28,
                current_health=28,
                defense=3,
                dodge=1,
                resistance=5,
                conversion_efficacy=35,
                attacks=[
                    _create_attack("melee", 6),
                    _create_attack("magic", 7),
                ],
                abilities=[],
                base_requirement=0,  # No experience progression
                tier_bonuses=[],
            ),
        },
        "rocky": {
            "Dwarf": Creature(
                name="Dwarf",
                symbol="D",
                color=(160, 140, 110),
                max_health=14,
                current_health=14,
                defense=3,
                dodge=1,
                resistance=2,
                conversion_efficacy=80,
                attacks=[
                    _create_attack("melee", 5),
                    _create_attack("ranged", 4, 1, 2, ["Splash"]),
                ],
                abilities=[],
                base_requirement=6,
                tier_bonuses=[
                    {"tier": 1, "battles": 6, "abilities": ["Shield Wall"]},
                    {
                        "tier": 2,
                        "battles": 12,
                        "defense": 1,
                        "dodge": 1,
                        "resistance": 1,
                        "melee_damage": 2,
                        "ranged_damage": 2,
                        "max_health": 4,
                    },
                ],
            ),
        },
        "trees": {
            "Frost Owl": Creature(
                name="Frost Owl",
                symbol="O",
                color=(180, 210, 235),
                max_health=9,
                current_health=9,
                defense=1,
                dodge=2,
                resistance=3,
                conversion_efficacy=55,
                attacks=[_create_attack("magic", 5, abilities=["Silencing"])],
                abilities=["Healing 3"],
                base_requirement=7,
                tier_bonuses=[
                    {"tier": 1, "battles": 7, "magic_damage": 1, "healing_bonus": 1},
                ],
            ),
        },
    },
    "underground": {
        "dirt": {
            "Skeleton": Creature(
                name="Skeleton",
                symbol="K",
                color=(200, 200, 200),
                max_health=11,
                current_health=11,
                defense=1,
                dodge=5,
                resistance=0,
                conversion_efficacy=30,
                attacks=[_create_attack("melee", 6)],
                abilities=[],
                base_requirement=0,  # No experience progression
                tier_bonuses=[],
            ),
        },
        "moss": {
            "Slime": Creature(
                name="Slime",
                symbol="S",
                color=(60, 150, 80),
                max_health=16,
                current_health=16,
                defense=2,
                dodge=1,
                resistance=3,
                conversion_efficacy=25,
                attacks=[_create_attack("ranged", 4, 1, 2, ["Defanging"])],
                abilities=[],
                base_requirement=10,
                tier_bonuses=[
                    {
                        "tier": 1,
                        "battles": 10,
                        "size": "2x2",
                        "glyphs": ["S", "S", "S", "S"],
                        "max_health": 16,
                        "defense": 2,
                        "dodge": 1,
                        "resistance": 3,
                        "conversion_efficacy": -10,
                        "ranged_damage": 6,
                    },
                ],
            ),
        },
        "stalactite": {
            "Bat": Creature(
                name="Bat",
                symbol="b",
                color=(90, 90, 110),
                max_health=7,
                current_health=7,
                defense=0,
                dodge=3,
                resistance=1,
                conversion_efficacy=40,
                attacks=[_create_attack("melee", 4)],
                abilities=["Lifelink"],
                base_requirement=6,
                tier_bonuses=[
                    {"tier": 1, "battles": 6, "melee_damage": 1, "max_health": 2},
                    {"tier": 2, "battles": 12, "dodge": 1, "melee_damage": 1, "max_health": 2},
                ],
            ),
        },
        "mushrooms": {
            # Safe terrain - no creatures
        },
    },
}

# Boss creatures (not terrain-specific)
BOSS_REGISTRY: dict[str, Creature] = {
    "Dragon King": Creature(
        name="Dragon King",
        symbol="D",
        color=(255, 80, 80),
        size="2x2",
        glyphs=["D", "D", "D", "D"],
        max_health=50,
        current_health=50,
        defense=6,
        dodge=6,
        resistance=10,
        conversion_efficacy=0,
        attacks=[
            _create_attack("melee", 7, abilities=["Piercing"]),
            _create_attack("ranged", 6, 1, 3, ["Splash"]),
            _create_attack("magic", 7, abilities=["Weakening"]),
        ],
        abilities=[],  # Special: moves randomly after attacking (handled in AI)
        base_requirement=0,
        tier_bonuses=[],
    ),
}


def get_creature_for_terrain(biome: str, terrain: str) -> Optional[Creature]:
    """Get a random creature template for the given biome/terrain.

    Returns a deep copy of the creature template, or None if no creatures exist
    for the given biome/terrain combination.
    """
    if biome in CREATURE_REGISTRY and terrain in CREATURE_REGISTRY[biome]:
        creatures = list(CREATURE_REGISTRY[biome][terrain].values())
        if creatures:
            return copy.deepcopy(random.choice(creatures))
    return None


def get_all_creatures_for_terrain(biome: str, terrain: str) -> list[str]:
    """Get all creature names available for a biome/terrain combination."""
    if biome in CREATURE_REGISTRY and terrain in CREATURE_REGISTRY[biome]:
        return list(CREATURE_REGISTRY[biome][terrain].keys())
    return []


def spawn_creature(name: str) -> Creature:
    """Create a new instance of a creature by name.

    Searches all biomes for the creature and returns a deep copy.
    Raises ValueError if creature not found.
    """
    # Check boss registry first
    if name in BOSS_REGISTRY:
        return copy.deepcopy(BOSS_REGISTRY[name])

    # Search all biomes
    for biome_data in CREATURE_REGISTRY.values():
        for terrain_data in biome_data.values():
            if name in terrain_data:
                return copy.deepcopy(terrain_data[name])

    raise ValueError(f"Unknown creature: {name}")


def get_boss(name: str) -> Optional[Creature]:
    """Get a boss creature by name. Returns a deep copy."""
    if name in BOSS_REGISTRY:
        return copy.deepcopy(BOSS_REGISTRY[name])
    return None


# Mapping of biomes to their terrain types and associated creatures
BIOME_TERRAIN_CREATURES: dict[str, dict[str, list[str]]] = {
    "forest": {
        "grass": ["Wolf"],
        "trees": ["Giant Spider"],
        "bushes": ["Goblin Pikeman"],
        "hill": ["Centaur Shaman"],
    },
    "plains": {
        "short_grass": ["Eagle"],
        "tall_grass": ["Lion", "Scorpion"],
    },
    "snow": {
        "snow": ["Yeti"],
        "rocky": ["Dwarf"],
        "trees": ["Frost Owl"],
    },
    "underground": {
        "dirt": ["Skeleton"],
        "moss": ["Slime"],
        "stalactite": ["Bat"],
        "mushrooms": [],  # Safe terrain
    },
}
