#!/usr/bin/env python3
"""A simple game using python-tcod where the player moves an @ symbol."""

from pathlib import Path
from abc import ABC, abstractmethod

import tcod


# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 25

# Font size settings
DEFAULT_FONT_SIZE = 32
FONT_ASPECT_RATIO = 0.625


class Screen(ABC):
    """Base class for screens in the game."""
    
    @abstractmethod
    def handle_event(self, event: tcod.event.Event, game: 'Game') -> None:
        """Handle an input event.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        pass
    
    @abstractmethod
    def render(self, console: tcod.console.Console, game: 'Game') -> None:
        """Render the screen to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        pass


class Player:
    """Represents the player in the game."""
    
    def __init__(self, x: int, y: int):
        """Initialize the player at the given position.
        
        Args:
            x: Initial x coordinate
            y: Initial y coordinate
        """
        self.x = x
        self.y = y
        self.symbol = '@'
    
    def move(self, dx: int, dy: int, grid_width: int = GRID_WIDTH, grid_height: int = GRID_HEIGHT) -> bool:
        """Attempt to move the player by the given delta.
        
        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
            grid_width: Width of the game grid
            grid_height: Height of the game grid
            
        Returns:
            True if the move was successful, False if out of bounds
        """
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check bounds
        if 0 <= new_x < grid_width and 0 <= new_y < grid_height:
            self.x = new_x
            self.y = new_y
            return True
        return False


class MapView(Screen):
    """Screen where the player moves around the map."""
    
    def __init__(self, player: Player):
        """Initialize the MapView screen.
        
        Args:
            player: The player object
        """
        self.player = player
        
        # Numpad direction mappings: key -> (dx, dy)
        self.direction_map = {
            tcod.event.KeySym.KP_4: (-1, 0),   # left
            tcod.event.KeySym.KP_6: (1, 0),    # right
            tcod.event.KeySym.KP_8: (0, -1),   # up
            tcod.event.KeySym.KP_2: (0, 1),    # down
            tcod.event.KeySym.KP_7: (-1, -1),  # upleft
            tcod.event.KeySym.KP_9: (1, -1),   # upright
            tcod.event.KeySym.KP_1: (-1, 1),   # downleft
            tcod.event.KeySym.KP_3: (1, 1),    # downright
        }
    
    def handle_event(self, event: tcod.event.Event, game: 'Game') -> None:
        """Handle an input event.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.Quit):
            game.running = False
        elif isinstance(event, tcod.event.KeyDown):
            # Check for Alt+Enter (fullscreen toggle)
            if event.sym == tcod.event.KeySym.RETURN and (
                event.mod & tcod.event.Modifier.LALT or event.mod & tcod.event.Modifier.RALT
            ):
                game.toggle_fullscreen()
            elif event.sym == tcod.event.KeySym.ESCAPE:
                game.running = False
            elif event.sym in self.direction_map:
                dx, dy = self.direction_map[event.sym]
                self.player.move(dx, dy, game.width, game.height)
    
    def render(self, console: tcod.console.Console, game: 'Game') -> None:
        """Render the map view to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        console.clear()
        
        # Draw border
        for x in range(game.width):
            console.print(x, 0, '-')
            console.print(x, game.height - 1, '-')
        for y in range(game.height):
            console.print(0, y, '|')
            console.print(game.width - 1, y, '|')
        
        # Draw corners
        console.print(0, 0, '+')
        console.print(game.width - 1, 0, '+')
        console.print(0, game.height - 1, '+')
        console.print(game.width - 1, game.height - 1, '+')
        
        # Draw instructions
        console.print(2, game.height - 2, "Use numpad to move. ESC to quit.")
        
        # Draw player symbol, make the color green
        console.print(self.player.x, self.player.y, self.player.symbol, fg=(0, 255, 0))


class MainMenu(Screen):
    """Main menu screen with options for New Game, Options, and Exit."""
    
    def __init__(self):
        """Initialize the MainMenu screen."""
        self.options = ["New Game", "Options", "Exit"]
        self.selected_index = 0
    
    def handle_event(self, event: tcod.event.Event, game: 'Game') -> None:
        """Handle an input event.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.Quit):
            game.running = False
        elif isinstance(event, tcod.event.KeyDown):
            # Check for Alt+Enter (fullscreen toggle)
            if event.sym == tcod.event.KeySym.RETURN and (
                event.mod & tcod.event.Modifier.LALT or event.mod & tcod.event.Modifier.RALT
            ):
                game.toggle_fullscreen()
            elif event.sym == tcod.event.KeySym.ESCAPE:
                game.running = False
            elif event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.KP_8):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.KP_2):
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                self._select_option(game)
    
    def _select_option(self, game: 'Game') -> None:
        """Handle selection of a menu option.
        
        Args:
            game: The game instance
        """
        selected = self.options[self.selected_index]
        if selected == "New Game":
            # Switch to MapView screen
            game.current_screen = game.map_view
        elif selected == "Options":
            # Placeholder for Options screen
            pass
        elif selected == "Exit":
            game.running = False
    
    def render(self, console: tcod.console.Console, game: 'Game') -> None:
        """Render the main menu to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        console.clear()
        
        # Draw title
        title = "MAIN MENU"
        title_x = (game.width - len(title)) // 2
        console.print(title_x, game.height // 4, title, fg=(255, 255, 0))
        
        # Draw menu options
        start_y = game.height // 2
        for i, option in enumerate(self.options):
            y = start_y + i * 2
            x = (game.width - len(option) - 4) // 2
            
            if i == self.selected_index:
                # Highlight selected option
                console.print(x, y, f"> {option} <", fg=(0, 255, 0))
            else:
                console.print(x + 2, y, option, fg=(200, 200, 200))
        
        # Draw instructions
        instructions = "Use UP/DOWN or numpad 8/2 to navigate. ENTER to select. ESC to quit."
        instr_x = (game.width - len(instructions)) // 2
        console.print(instr_x, game.height - 3, instructions, fg=(150, 150, 150))


class Game:
    """Main game class."""
    
    def __init__(self, context=None, font_path=None):
        """Initialize the game.
        
        Args:
            context: The tcod.context.Context for the game (optional)
            font_path: Path to the font file (optional)
        """
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.player = Player(self.width // 2, self.height // 2)
        self.running = True
        self.context = context
        self.font_path = font_path
        self.font_size = DEFAULT_FONT_SIZE
        
        # Initialize screens
        self.map_view = MapView(self.player)
        self.main_menu = MainMenu()
        self.current_screen = self.main_menu

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
        self.current_screen.handle_event(event, self)
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the game by delegating to the current screen.
        
        Args:
            console: The console to render to
        """
        self.current_screen.render(console, self)


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
