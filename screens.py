#!/usr/bin/env python3
"""Screen classes for the game."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import tcod

if TYPE_CHECKING:
    import game


class Screen(ABC):
    """Base class for screens in the game."""
    
    def handle_event(self, event: tcod.event.Event, game: 'game.Game') -> None:
        """Handle an input event.
        
        This method handles common events (Alt+Enter for fullscreen, Escape for quit)
        before delegating to handle_specific_event for screen-specific handling.
        
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
            else:
                # Delegate to screen-specific event handling
                self.handle_specific_event(event, game)
        else:
            # Delegate other event types to screen-specific handling
            self.handle_specific_event(event, game)
    
    @abstractmethod
    def handle_specific_event(self, event: tcod.event.Event, game: 'game.Game') -> None:
        """Handle a screen-specific input event.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        pass
    
    @abstractmethod
    def render(self, console: tcod.console.Console, game: 'game.Game') -> None:
        """Render the screen to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        pass


class MapView(Screen):
    """Screen where the player moves around the map."""
    
    def __init__(self):
        """Initialize the MapView screen."""
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
    
    def handle_specific_event(self, event: tcod.event.Event, game: 'game.Game') -> None:
        """Handle map-specific input events.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in self.direction_map:
                # Import here to avoid circular import at module level
                import game as gm
                dx, dy = self.direction_map[event.sym]
                game.gamestate = gm.advance_step(game.gamestate, (dx, dy))
                
                # Check if an encounter was triggered
                if game.gamestate.active_encounter is not None:
                    game.current_back_screen = game.encounter_screen
    
    def render(self, console: tcod.console.Console, game: 'game.Game') -> None:
        """Render the map view to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        # Import here to avoid circular import at module level
        import game as gm
        
        console.clear()
        
        # Draw border
        for x in range(gm.GRID_WIDTH):
            console.print(x, 0, '-')
            console.print(x, gm.GRID_HEIGHT - 1, '-')
        for y in range(gm.GRID_HEIGHT):
            console.print(0, y, '|')
            console.print(gm.GRID_WIDTH - 1, y, '|')
        
        # Draw corners
        console.print(0, 0, '+')
        console.print(gm.GRID_WIDTH - 1, 0, '+')
        console.print(0, gm.GRID_HEIGHT - 1, '+')
        console.print(gm.GRID_WIDTH - 1, gm.GRID_HEIGHT - 1, '+')
        
        # Draw instructions
        console.print(2, gm.GRID_HEIGHT - 2, "Use numpad to move. ESC to quit.")
        
        # Draw placed placeables if they are visible
        for placeable in game.gamestate.placeables or []:
            if isinstance(placeable, gm.Visible):
                self._draw_visible(console, placeable)

        # Draw the player on top
        for placeable in game.gamestate.placeables or []:
            if isinstance(placeable, gm.Player):
                self._draw_visible(console, placeable)

    def _draw_visible(self, console: tcod.console.Console, visible: 'game.Visible') -> None:
        """Draw a visible object on the console.
        
        Args:
            console: The console to draw on
            visible: The visible object to draw
        """
        console.print(visible.x, visible.y, visible.symbol, fg=visible.color)


class EncounterScreen(Screen):
    """Screen shown when the player encounters something."""
    
    def handle_specific_event(self, event: tcod.event.Event, game: 'game.Game') -> None:
        """Handle encounter-specific input events.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER, tcod.event.KeySym.SPACE):
                # Clear the active encounter and return to map
                game.gamestate.active_encounter = None
                game.current_back_screen = game.map_view
    
    def render(self, console: tcod.console.Console, game: 'game.Game') -> None:
        """Render the encounter screen to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        # Import here to avoid circular import at module level
        import game as gm
        
        console.clear()
        
        # Draw title
        title = "ENCOUNTER!"
        title_x = (gm.GRID_WIDTH - len(title)) // 2
        console.print(title_x, gm.GRID_HEIGHT // 3, title, fg=(255, 255, 0))
        
        # Draw message
        message = "You encountered something!"
        message_x = (gm.GRID_WIDTH - len(message)) // 2
        console.print(message_x, gm.GRID_HEIGHT // 2, message, fg=(200, 200, 200))
        
        # Draw instructions
        instructions = "Press ENTER or SPACE to return to map"
        instr_x = (gm.GRID_WIDTH - len(instructions)) // 2
        console.print(instr_x, gm.GRID_HEIGHT - 3, instructions, fg=(150, 150, 150))


class MainMenu(Screen):
    """Main menu screen with options for New Game, Options, and Exit."""
    
    def __init__(self):
        """Initialize the MainMenu screen."""
        self.options = ["New Game", "Options", "Exit"]
        self.selected_index = 0
    
    def handle_specific_event(self, event: tcod.event.Event, game: 'game.Game') -> None:
        """Handle main menu-specific input events.
        
        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.KP_8):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.KP_2):
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                self._select_option(game)
    
    def _select_option(self, game: 'game.Game') -> None:
        """Handle selection of a menu option.
        
        Args:
            game: The game instance
        """
        selected = self.options[self.selected_index]
        if selected == "New Game":
            # Switch to MapView screen
            game.current_back_screen = game.map_view
        elif selected == "Options":
            # Placeholder for Options screen
            pass
        elif selected == "Exit":
            game.running = False
    
    def render(self, console: tcod.console.Console, game: 'game.Game') -> None:
        """Render the main menu to the console.
        
        Args:
            console: The console to render to
            game: The game instance
        """
        # Import here to avoid circular import at module level
        import game as gm
        
        console.clear()
        
        # Draw title
        title = "MAIN MENU"
        title_x = (gm.GRID_WIDTH - len(title)) // 2
        console.print(title_x, gm.GRID_HEIGHT // 4, title, fg=(255, 255, 0))
        
        # Draw menu options
        start_y = gm.GRID_HEIGHT // 2
        for i, option in enumerate(self.options):
            y = start_y + i * 2
            x = (gm.GRID_WIDTH - len(option) - 4) // 2
            
            if i == self.selected_index:
                # Highlight selected option
                console.print(x, y, f"> {option} <", fg=(0, 255, 0))
            else:
                console.print(x + 2, y, option, fg=(200, 200, 200))
        
        # Draw instructions
        instructions = "Use UP/DOWN or numpad 8/2 to navigate."
        instr_x = (gm.GRID_WIDTH - len(instructions)) // 2
        console.print(instr_x, gm.GRID_HEIGHT - 3, instructions, fg=(150, 150, 150))
        instructions_two = "ENTER to select. ESC to quit."
        instr_x_two = (gm.GRID_WIDTH - len(instructions_two)) // 2
        console.print(instr_x_two, gm.GRID_HEIGHT - 2, instructions_two, fg=(150, 150, 150))
