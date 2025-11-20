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


@dataclass
class Visible(Placeable):
    """A base class for visible objects on the grid."""
    symbol: str
    color: tuple[int, int, int]


@dataclass
class Invisible(Placeable):
    """A base class for invisible objects on the grid."""
    pass


@dataclass
class Terrain(Visible):
    """Represents terrain tiles on the map."""
    pass


@dataclass
class Encounter(Invisible):
    """Represents an invisible encounter trigger on the map."""
    pass


@dataclass
class Player(Visible):
    """Represents the player in the game."""
    symbol: str = '@'
    color: tuple[int, int, int] = (0, 255, 0)
    name: str = "Player"


@dataclass
class GameState:
    """Serializable gamestate data."""
    placeables: list[Placeable]
    active_encounter: Optional[Encounter]