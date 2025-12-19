"""Data classes and constants for the game."""

from dataclasses import dataclass, field
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
    bg_color: Optional[tuple[int, int, int]] = None


@dataclass
class Terrain(Placeable):
    """Represents terrain tiles on the map."""

    visible: bool = True

@dataclass
class Exit(Placeable):
    """Represents the exit to the next level."""
    visible: bool = True
    symbol: str = ">"
    color: tuple[int, int, int] = (255, 255, 255)


@dataclass
class Attack:
    """Represents a single attack a creature can perform."""

    attack_type: str  # "melee" | "ranged" | "magic"
    damage: int
    range_min: Optional[int] = None  # For ranged attacks
    range_max: Optional[int] = None
    abilities: list[str] = field(default_factory=list)  # Piercing, Splash, Weakening, etc.


@dataclass
class Creature:
    """Represents a creature that can be encountered or on the player's team."""

    # Identity
    name: str
    symbol: str
    color: tuple[int, int, int]

    # Size support for 2x2 units
    size: str = "1x1"  # "1x1" or "2x2"
    glyphs: Optional[list[str]] = None  # [TL, TR, BL, BR] for 2x2 units

    # Combat stats
    max_health: int = 10
    current_health: int = 10
    defense: int = 0  # vs melee
    dodge: int = 0  # vs ranged
    resistance: int = 0  # vs magic

    # Attacks & abilities
    attacks: list[Attack] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)  # Passive abilities

    # Conversion
    conversion_efficacy: int = 50  # 0-100
    conversion_progress: int = 0  # Progress toward conversion

    # Combat state
    debuffs: dict[str, int] = field(default_factory=dict)  # {"weakened": 2} - stacks

    # Experience/Progression
    tier: int = 0  # 0, 1, 2, or 3
    battles_completed: int = 0
    base_requirement: int = 5  # Base battles needed for tier 1
    tier_bonuses: list[dict] = field(default_factory=list)  # Per-tier stat/ability unlocks


@dataclass
class Encounter(Placeable):
    """Represents an encounter trigger on the map."""

    visible: bool = False
    creatures: list[Creature] = None  # Enemy creatures to spawn (placed randomly on init)
    player_team: list[Optional["Creature | Player"]] = None  # 9 cells: TL, T, TR, L, M, R, BL, B, BR
    enemy_team: list[Optional[Creature]] = None  # 9 cells: TL, T, TR, L, M, R, BL, B, BR

    # Combat state
    current_turn: str = "player"  # "player" | "enemy"
    turn_number: int = 0
    combat_log: list[str] = None  # Log of combat events

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.creatures is None:
            self.creatures = []
        if self.player_team is None:
            self.player_team = [None] * 9
        if self.enemy_team is None:
            self.enemy_team = [None] * 9
        if self.combat_log is None:
            self.combat_log = []


@dataclass
class Player(Placeable):
    """Represents the player in the game."""

    visible: bool = True
    symbol: str = "@"
    color: tuple[int, int, int] = (0, 255, 0)
    name: str = "Player"

    # Hero attributes (affect allies and hero combat)
    intelligence: int = 0  # Reduces tier requirements, boosts ranged attack/dodge
    wisdom: int = 0  # +1 all defenses per +4 to allies, boosts melee attack/defense
    charisma: int = 0  # +10% efficacy per +4, boosts magic attack/resistance
    battle: int = 0  # Scales hero combat effectiveness

    # Base combat stats (heroes can use all 3 attack types)
    base_melee_attack: int = 5
    base_ranged_attack: int = 5
    base_magic_attack: int = 5
    base_defense: int = 3
    base_dodge: int = 3
    base_resistance: int = 3

    # Health
    max_health: int = 100
    current_health: int = 100

    # Class and level
    player_class: str = "Adventurer"
    level: int = 1
    stat_points: int = 0  # +3 per floor

    # Team
    creatures: list[Optional[Creature]] = None

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.creatures is None:
            self.creatures = [None] * 9


@dataclass
class GameState:
    """Serializable gamestate data."""

    placeables: list[Placeable]
    active_encounter: Optional[Encounter]
    current_stage: int = 1
    max_stages: int = 20
    status: str = "playing"  # playing, won, lost
    biome_order: list[str] = None
    run_seed: Optional[int] = None
    pending_recruits: list[Creature] = None
    last_battle_results: Optional[dict] = None  # Results from last battle for display
    pending_next_stage: bool = False  # True when player used exit and needs to advance after stat allocation

    def __post_init__(self):
        if self.pending_recruits is None:
            self.pending_recruits = []
