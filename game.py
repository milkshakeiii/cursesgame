#!/usr/bin/env python3
"""A simple game using python-tcod where the player moves an @ symbol."""

from pathlib import Path

import tcod

from screens import Screen, MapView, EncounterScreen, EncounterStartScreen, MainMenu
from game_data import GRID_WIDTH, GRID_HEIGHT
from gameplay import generate_map


# Font size settings
DEFAULT_FONT_SIZE = 32
FONT_ASPECT_RATIO = 0.625


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
        self.encounter_start_screen = EncounterStartScreen()
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
