#!/usr/bin/env python3
"""A simple game using python-tcod where the player moves an @ symbol."""

from pathlib import Path

import tcod


# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 25

# Font size settings
DEFAULT_FONT_SIZE = 32
FONT_ASPECT_RATIO = 0.625


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

    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed mode."""
        if not self.context:
            return
        
        window = self.context.sdl_window
        if not window:
            return
        
        window.fullscreen = not window.fullscreen
    
    def handle_event(self, event: tcod.event.Event) -> None:
        """Handle an input event.
        
        Args:
            event: The event to handle
        """
        if isinstance(event, tcod.event.Quit):
            self.running = False
        elif isinstance(event, tcod.event.KeyDown):
            # Check for Alt+Enter (fullscreen toggle)
            if event.sym == tcod.event.KeySym.RETURN and (
                event.mod & tcod.event.Modifier.LALT or event.mod & tcod.event.Modifier.RALT
            ):
                self.toggle_fullscreen()
            elif event.sym == tcod.event.KeySym.ESCAPE:
                self.running = False
            elif event.sym in self.direction_map:
                dx, dy = self.direction_map[event.sym]
                self.player.move(dx, dy, self.width, self.height)
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the game to the console.
        
        Args:
            console: The console to render to
        """
        console.clear()
        
        # Draw border
        for x in range(self.width):
            console.print(x, 0, '-')
            console.print(x, self.height - 1, '-')
        for y in range(self.height):
            console.print(0, y, '|')
            console.print(self.width - 1, y, '|')
        
        # Draw corners
        console.print(0, 0, '+')
        console.print(self.width - 1, 0, '+')
        console.print(0, self.height - 1, '+')
        console.print(self.width - 1, self.height - 1, '+')
        
        # Draw instructions
        console.print(2, self.height - 2, "Use numpad to move. ESC to quit.")
        
        # Draw player symbol, make the color green
        console.print(self.player.x, self.player.y, self.player.symbol, fg=(0, 255, 0))


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
