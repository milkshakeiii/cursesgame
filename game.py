#!/usr/bin/env python3
"""A simple game using python-tcod where the player moves an @ symbol."""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import tcod
from tcod import color

from screens import Screen, MapView, EncounterScreen, MainMenu


# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 25

# Font size settings
DEFAULT_FONT_SIZE = 32
FONT_ASPECT_RATIO = 0.625


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
    placeables: list[Placeable] = None
    active_encounter: Optional[Encounter] = None


def generate_map() -> GameState:
    """Generate a map with terrain, encounters, and a player.
    
    Returns:
        A GameState with placeables including terrain, encounters, and player.
    """
    placeables = []
    
    # Add player at center
    placeables.append(Player(x=GRID_WIDTH // 2, y=GRID_HEIGHT // 2))
    
    # Add terrain tiles throughout the map
    # Create a pattern of grass (,) and rocky (.) terrain
    for y in range(1, GRID_HEIGHT - 1):
        for x in range(1, GRID_WIDTH - 1):
            # Create a pattern: grass in some areas, rocky in others
            if (x + y) % 3 == 0:
                placeables.append(Terrain(x=x, y=y, symbol=',', color=(50, 150, 50)))
            else:
                placeables.append(Terrain(x=x, y=y, symbol='.', color=(150, 150, 150)))
    
    # Add some encounters on random tiles
    # Place encounters at specific locations for now
    encounter_positions = [
        (10, 10), (15, 12), (30, 8), (20, 15), (35, 18), (8, 20)
    ]
    for x, y in encounter_positions:
        placeables.append(Encounter(x=x, y=y))
    
    return GameState(placeables=placeables)


def advance_step(gamestate: GameState, action: Optional[tuple[int, int]]) -> GameState:
    """Advance the game by one step based on the player action.
    
    Args:
        gamestate: The current game state
        action: A tuple of (dx, dy) representing the player's movement, or None for no action
        
    Returns:
        The updated game state
    """
    if action is None:
        return gamestate

    player = None
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            player = placeable
            break
    if player is None:
        raise ValueError("No player found in gamestate.")
    
    dx, dy = action
    new_x = player.x + dx
    new_y = player.y + dy
    
    # Check bounds and update position if valid
    if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
        player.x = new_x
        player.y = new_y
        
        # Check if player stepped on an encounter
        for placeable in gamestate.placeables or []:
            if isinstance(placeable, Encounter):
                if placeable.x == player.x and placeable.y == player.y:
                    gamestate.active_encounter = placeable
                    break
    
    return gamestate







class Game:
    """Main game class."""
    
    def __init__(self, context=None, font_path=None):
        """Initialize the game.
        
        Args:
            context: The tcod.context.Context for the game (optional)
            font_path: Path to the font file (optional)
        """
        self.gamestate = generate_map()
        self.running = True
        self.context = context
        self.font_path = font_path
        self.font_size = DEFAULT_FONT_SIZE
        
        # Initialize screens
        self.map_view = MapView()
        self.main_menu = MainMenu()
        self.encounter_screen = EncounterScreen()
        self.current_back_screen = self.main_menu
        self.current_front_screen = None

    def current_screen(self) -> Screen:
        """Get the current active screen."""
        return self.current_front_screen or self.current_back_screen

    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed mode."""
        if not self.context:
            return
        
        window = self.context.sdl_window
        if not window:
            return
        
        window.fullscreen = not window.fullscreen
    
    def handle_event(self, event: tcod.event.Event) -> None:
        """Handle an input event by delegating to the current screen.
        
        Args:
            event: The event to handle
        """
        self.current_screen().handle_event(event, self)
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the game by delegating to the current screen.
        
        Args:
            console: The console to render to
        """
        self.current_screen().render(console, self)


def main():
    """Main entry point for the game."""
    THIS_DIR = Path(__file__, "..")  # Directory of this script file
    FONT = THIS_DIR / "5x8.bdf"
    
    tileset = tcod.tileset.load_bdf(
        FONT
    )
    
    with tcod.context.new(
        columns=GRID_WIDTH,
        rows=GRID_HEIGHT,
        tileset=tileset,
        title="Simple Movement Game",
        vsync=True,
    ) as context:
        console = tcod.console.Console(GRID_WIDTH, GRID_HEIGHT, order="F")
        game = Game(context=context, font_path=FONT)
        
        while game.running:
            console.clear()
            game.render(console)
            context.present(console, keep_aspect=True, integer_scaling=False)
            
            for event in tcod.event.wait():
                context.convert_event(event)
                game.handle_event(event)


if __name__ == "__main__":
    main()
