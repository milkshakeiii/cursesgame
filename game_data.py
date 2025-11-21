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
class Encounter(Placeable):
    """Represents an encounter trigger on the map."""

    visible: bool = False


@dataclass
class Player(Placeable):
    """Represents the player in the game."""

    visible: bool = True
    symbol: str = "@"
    color: tuple[int, int, int] = (0, 255, 0)
    name: str = "Player"


@dataclass
class GameState:
    """Serializable gamestate data."""

    placeables: list[Placeable]
    active_encounter: Optional[Encounter]
