"""Data classes and constants for the game."""

from dataclasses import dataclass
from typing import Optional

# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 25


@dataclass
class Placeable:
    """A base class for objects that can be placed on the grid."""

    x: int
    y: int
    symbol: str
    color: tuple[int, int, int]
    visible: bool


@dataclass
class Terrain(Placeable):
    """Represents terrain tiles on the map."""

    visible: bool = True


@dataclass
class Creature:
    """Represents a creature that can be encountered or on the player's team."""

    name: str
    symbol: str
    color: tuple[int, int, int]
    strength: int
    dexterity: int
    constitution: int
    active_abilities: list[str]
    passive_abilities: list[str]
    max_health: int
    current_health: int
    current_convert: int  # out of 100
    level: int


@dataclass
class Encounter(Placeable):
    """Represents an encounter trigger on the map."""

    visible: bool = False
    creature: Optional[Creature] = None


@dataclass
class Player(Placeable):
    """Represents the player in the game."""

    visible: bool = True
    symbol: str = "@"
    color: tuple[int, int, int] = (0, 255, 0)
    name: str = "Player"
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    active_abilities: list[str] = None
    passive_abilities: list[str] = None
    max_health: int = 100
    current_health: int = 100
    player_class: str = "Adventurer"
    level: int = 1
    creatures: list[Creature] = None

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.active_abilities is None:
            self.active_abilities = []
        if self.passive_abilities is None:
            self.passive_abilities = []
        if self.creatures is None:
            self.creatures = []


@dataclass
class GameState:
    """Serializable gamestate data."""

    placeables: list[Placeable]
    active_encounter: Optional[Encounter]
