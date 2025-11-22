#!/usr/bin/env python3
"""Screen classes for the game."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tcod

from game_data import GRID_HEIGHT, GRID_WIDTH, Player, Creature
from gameplay import advance_step

if TYPE_CHECKING:
    import game

# Constants for encounter grid
ENCOUNTER_GRID_WIDTH = 3  # 3x3 grid for each side
ENCOUNTER_GRID_HEIGHT = 3


def is_within_console_bounds(x: int, y: int) -> bool:
    """Check if coordinates are within console bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
    
    Returns:
        True if coordinates are within bounds, False otherwise
    """
    return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT


class Screen(ABC):
    """Base class for screens in the game."""

    def handle_event(self, event: tcod.event.Event, game: "game.Game") -> None:
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
    def handle_specific_event(self, event: tcod.event.Event, game: "game.Game") -> None:
        """Handle a screen-specific input event.

        Args:
            event: The event to handle
            game: The game instance
        """

    @abstractmethod
    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the screen to the console.

        Args:
            console: The console to render to
            game: The game instance
        """


class MapView(Screen):
    """Screen where the player moves around the map."""

    def __init__(self):
        """Initialize the MapView screen."""
        # Numpad direction mappings: key -> (dx, dy)
        self.direction_map = {
            tcod.event.KeySym.KP_4: (-1, 0),  # left
            tcod.event.KeySym.KP_6: (1, 0),  # right
            tcod.event.KeySym.KP_8: (0, -1),  # up
            tcod.event.KeySym.KP_2: (0, 1),  # down
            tcod.event.KeySym.KP_7: (-1, -1),  # upleft
            tcod.event.KeySym.KP_9: (1, -1),  # upright
            tcod.event.KeySym.KP_1: (-1, 1),  # downleft
            tcod.event.KeySym.KP_3: (1, 1),  # downright
        }

    def handle_specific_event(self, event: tcod.event.Event, game: "game.Game") -> None:
        """Handle map-specific input events.

        Processes numpad keys for 8-directional player movement. When the player
        moves onto an encounter tile, switches to the encounter start screen.

        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in self.direction_map:
                dx, dy = self.direction_map[event.sym]
                game.gamestate = advance_step(game.gamestate, ("move", dx, dy))

                # Check if an encounter was triggered
                if game.gamestate.active_encounter is not None:
                    game.current_back_screen = game.encounter_start_screen

    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the map view to the console.

        Args:
            console: The console to render to
            game: The game instance
        """

        console.clear()

        # Draw border
        for x in range(GRID_WIDTH):
            console.print(x, 0, "-")
            console.print(x, GRID_HEIGHT - 1, "-")
        for y in range(GRID_HEIGHT):
            console.print(0, y, "|")
            console.print(GRID_WIDTH - 1, y, "|")

        # Draw corners
        console.print(0, 0, "+")
        console.print(GRID_WIDTH - 1, 0, "+")
        console.print(0, GRID_HEIGHT - 1, "+")
        console.print(GRID_WIDTH - 1, GRID_HEIGHT - 1, "+")

        # Draw instructions
        console.print(2, GRID_HEIGHT - 2, "Use numpad to move. ESC to quit.")

        # Draw placed placeables if they are visible
        for placeable in game.gamestate.placeables or []:
            if placeable.visible and not isinstance(placeable, Player):
                self._draw_placeable(console, placeable)

        # Draw the player on top
        for placeable in game.gamestate.placeables or []:
            if isinstance(placeable, Player):
                self._draw_placeable(console, placeable)

    def _draw_placeable(self, console: tcod.console.Console, placeable: "game.Placeable") -> None:
        """Draw a visible object on the console.

        Args:
            console: The console to draw on
            placeable: The visible object to draw
        """
        console.print(placeable.x, placeable.y, placeable.symbol, fg=placeable.color)


class EncounterStartScreen(Screen):
    """Screen shown when the player first encounters something."""

    def handle_specific_event(self, event: tcod.event.Event, game: "game.Game") -> None:
        """Handle encounter start screen-specific input events.

        Waits for the player to press Enter or Space to continue to the
        main encounter screen.

        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in (
                tcod.event.KeySym.RETURN,
                tcod.event.KeySym.KP_ENTER,
                tcod.event.KeySym.SPACE,
            ):
                # Continue to main encounter screen
                game.current_back_screen = game.encounter_screen

    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the encounter start screen to the console.

        Args:
            console: The console to render to
            game: The game instance
        """

        console.clear()

        # Draw title
        title = "ENCOUNTER!"
        title_x = (GRID_WIDTH - len(title)) // 2
        console.print(title_x, GRID_HEIGHT // 3, title, fg=(255, 255, 0))

        # Draw message
        message = "You encountered something!"
        message_x = (GRID_WIDTH - len(message)) // 2
        console.print(message_x, GRID_HEIGHT // 2, message, fg=(200, 200, 200))

        # Draw instructions
        instructions = "Press ENTER or SPACE to continue"
        instr_x = (GRID_WIDTH - len(instructions)) // 2
        console.print(instr_x, GRID_HEIGHT - 3, instructions, fg=(150, 150, 150))


class EncounterScreen(Screen):
    """Main tactical battle screen for encounters."""

    def __init__(self):
        """Initialize the EncounterScreen."""
        self.action_mode = None  # "attack" or "convert" when selecting target
        self.selection_mode = None  # "selecting_ally", "selecting_enemy", or None
        self.selected_side = "enemy"  # "player" or "enemy"
        self.selected_index = 4  # Index 0-8 in the grid (default to middle)
        self.target_selection_map = {
            tcod.event.KeySym.KP_7: (0, 0),  # top-left
            tcod.event.KeySym.KP_8: (1, 0),  # top-center
            tcod.event.KeySym.KP_9: (2, 0),  # top-right
            tcod.event.KeySym.KP_4: (0, 1),  # middle-left
            tcod.event.KeySym.KP_5: (1, 1),  # middle-center
            tcod.event.KeySym.KP_6: (2, 1),  # middle-right
            tcod.event.KeySym.KP_1: (0, 2),  # bottom-left
            tcod.event.KeySym.KP_2: (1, 2),  # bottom-center
            tcod.event.KeySym.KP_3: (2, 2),  # bottom-right
        }

    def handle_specific_event(self, event: tcod.event.Event, game: "game.Game") -> None:
        """Handle encounter screen-specific input events.

        Processes combat actions (A for attack, C for convert) and allows
        fleeing (F key) which returns to the map view.
        Q to select allies, E to select enemies.

        Args:
            event: The event to handle
            game: The game instance
        """
        if isinstance(event, tcod.event.KeyDown):
            # If in target selection mode (for attack/convert), handle numpad input
            if self.action_mode in ("attack", "convert"):
                if event.sym in self.target_selection_map:
                    # Get the target coordinates
                    target_x, target_y = self.target_selection_map[event.sym]
                    
                    # Execute the action through advance_step
                    game.gamestate = advance_step(game.gamestate, (self.action_mode, target_x, target_y))
                    
                    # Exit selection mode
                    self.action_mode = None
                    
                    # Check if encounter ended (all creatures defeated or converted)
                    if game.gamestate.active_encounter is None:
                        game.current_back_screen = game.map_view
                elif event.sym == tcod.event.KeySym.ESCAPE:
                    # Cancel target selection
                    self.action_mode = None
            # If in ally/enemy selection mode, handle numpad input
            elif self.selection_mode in ("selecting_ally", "selecting_enemy"):
                if event.sym in self.target_selection_map:
                    # Get the grid position
                    grid_x, grid_y = self.target_selection_map[event.sym]
                    grid_index = grid_y * ENCOUNTER_GRID_WIDTH + grid_x
                    
                    # Update selection
                    if self.selection_mode == "selecting_ally":
                        self.selected_side = "player"
                    else:
                        self.selected_side = "enemy"
                    self.selected_index = grid_index
                    
                    # Exit selection mode
                    self.selection_mode = None
                elif event.sym == tcod.event.KeySym.ESCAPE:
                    # Cancel selection
                    self.selection_mode = None
            else:
                # Normal mode - handle action/selection keys
                if event.sym == tcod.event.KeySym.A:
                    # Enter attack target selection mode (only enemies)
                    self.action_mode = "attack"
                elif event.sym == tcod.event.KeySym.C:
                    # Enter convert target selection mode (only enemies)
                    self.action_mode = "convert"
                elif event.sym == tcod.event.KeySym.Q:
                    # Enter ally selection mode
                    self.selection_mode = "selecting_ally"
                elif event.sym == tcod.event.KeySym.E:
                    # Enter enemy selection mode
                    self.selection_mode = "selecting_enemy"
                elif event.sym == tcod.event.KeySym.F:
                    # Flee - return to map
                    game.gamestate.active_encounter = None
                    game.current_back_screen = game.map_view

    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the encounter screen to the console.

        Args:
            console: The console to render to
            game: The game instance
        """
        console.clear()

        # Calculate layout dimensions
        # Left half is the info panel
        info_panel_width = GRID_WIDTH // 2
        # Right half is split into top and bottom
        right_panel_x = info_panel_width
        right_panel_width = GRID_WIDTH - info_panel_width
        top_panel_height = GRID_HEIGHT // 2

        # Draw vertical divider between left and right
        for y in range(GRID_HEIGHT):
            console.print(info_panel_width, y, "|", fg=(100, 100, 100))

        # Draw horizontal divider in right panel
        for x in range(right_panel_x + 1, GRID_WIDTH):
            console.print(x, top_panel_height, "-", fg=(100, 100, 100))

        # Get selected creature info for info panel
        selected_creature = None
        selected_name = None
        if game.gamestate.active_encounter is not None:
            if self.selected_side == "player":
                team = game.gamestate.active_encounter.player_team
                if team and self.selected_index < len(team):
                    entity = team[self.selected_index]
                    if isinstance(entity, Creature):
                        selected_creature = entity
                        selected_name = entity.name
                    elif isinstance(entity, Player):
                        selected_name = "Player"
            else:  # enemy side
                team = game.gamestate.active_encounter.enemy_team
                if team and self.selected_index < len(team):
                    entity = team[self.selected_index]
                    if isinstance(entity, Creature):
                        selected_creature = entity
                        selected_name = entity.name

        # LEFT PANEL: Info panel - show selected creature info
        console.print(2, 1, "BATTLE INFO", fg=(255, 255, 0))
        
        if selected_creature:
            side_label = "Ally" if self.selected_side == "player" else "Enemy"
            console.print(2, 3, f"{side_label}: {selected_name}", fg=(200, 200, 200))
            health_color = (0, 255, 0) if selected_creature.current_health > 30 else (255, 100, 100)
            console.print(2, 4, f"HP: {selected_creature.current_health}/{selected_creature.max_health}", fg=health_color)
            console.print(2, 5, f"Convert: {selected_creature.current_convert}/100", fg=(150, 150, 255))
        elif selected_name == "Player":
            # Show player info
            player = None
            for placeable in game.gamestate.placeables or []:
                if isinstance(placeable, Player):
                    player = placeable
                    break
            if player:
                console.print(2, 3, f"Player", fg=(200, 200, 200))
                health_color = (0, 255, 0) if player.current_health > 30 else (255, 100, 100)
                console.print(2, 4, f"HP: {player.current_health}/{player.max_health}", fg=health_color)
        else:
            console.print(2, 3, "No selection", fg=(200, 200, 200))

        # UPPER RIGHT: 6x3 grid with player team on left and enemy team on right
        grid_width = 6
        grid_height = 3
        grid_start_x = right_panel_x + (right_panel_width - grid_width) // 2
        grid_start_y = 2

        # Draw grid border
        for x in range(grid_width):
            console.print(grid_start_x + x, grid_start_y, "-", fg=(100, 100, 100))
            console.print(grid_start_x + x, grid_start_y + grid_height + 1, "-", fg=(100, 100, 100))
        for y in range(grid_height + 2):
            console.print(grid_start_x - 1, grid_start_y + y, "|", fg=(100, 100, 100))
            console.print(grid_start_x + grid_width, grid_start_y + y, "|", fg=(100, 100, 100))

        # Draw corners
        console.print(grid_start_x - 1, grid_start_y, "+", fg=(100, 100, 100))
        console.print(grid_start_x + grid_width, grid_start_y, "+", fg=(100, 100, 100))
        console.print(grid_start_x - 1, grid_start_y + grid_height + 1, "+", fg=(100, 100, 100))
        console.print(
            grid_start_x + grid_width, grid_start_y + grid_height + 1, "+", fg=(100, 100, 100)
        )

        # Draw entities from teams
        if game.gamestate.active_encounter is not None:
            # Draw player team (left 3x3)
            player_team = game.gamestate.active_encounter.player_team
            if player_team:
                for i in range(9):
                    grid_x = i % 3
                    grid_y = i // 3
                    screen_x = grid_start_x + grid_x
                    screen_y = grid_start_y + 1 + grid_y
                    
                    entity = player_team[i]
                    if entity:
                        # Determine symbol and color
                        if isinstance(entity, Player):
                            symbol = "@"
                            color = (0, 255, 0)
                        else:
                            symbol = entity.symbol
                            color = entity.color
                        
                        # Check if this is the selected entity
                        is_selected = (self.selected_side == "player" and self.selected_index == i)
                        bg_color = (100, 100, 50) if is_selected else (0, 0, 0)
                        
                        console.print(screen_x, screen_y, symbol, fg=color, bg=bg_color)

            # Draw enemy team (right 3x3)
            enemy_team = game.gamestate.active_encounter.enemy_team
            if enemy_team:
                for i in range(9):
                    grid_x = i % 3
                    grid_y = i // 3
                    screen_x = grid_start_x + 3 + grid_x
                    screen_y = grid_start_y + 1 + grid_y
                    
                    entity = enemy_team[i]
                    if entity:
                        symbol = entity.symbol
                        color = entity.color
                        
                        # Check if this is the selected entity
                        is_selected = (self.selected_side == "enemy" and self.selected_index == i)
                        bg_color = (100, 100, 50) if is_selected else (0, 0, 0)
                        
                        console.print(screen_x, screen_y, symbol, fg=color, bg=bg_color)

        # Highlight appropriate side based on mode
        if self.action_mode in ("attack", "convert"):
            # Highlight enemy side for attack/convert
            highlight_color = (255, 255, 100) if self.action_mode == "attack" else (150, 150, 255)
            for dy in range(grid_height):
                for dx in range(ENCOUNTER_GRID_WIDTH, grid_width):
                    x = grid_start_x + dx
                    y = grid_start_y + dy + 1
                    # Bounds check before accessing console arrays
                    if is_within_console_bounds(x, y):
                        # Get current character and preserve it while changing background
                        current_char = chr(console.ch[x, y]) if console.ch[x, y] != 0 else " "
                        current_fg = tuple(console.fg[x, y])
                        console.print(x, y, current_char, fg=current_fg, bg=highlight_color)
        elif self.selection_mode == "selecting_ally":
            # Highlight player side
            highlight_color = (100, 150, 255)
            for dy in range(grid_height):
                for dx in range(ENCOUNTER_GRID_WIDTH):
                    x = grid_start_x + dx
                    y = grid_start_y + dy + 1
                    # Bounds check before accessing console arrays
                    if is_within_console_bounds(x, y):
                        # Get current character and preserve it while changing background
                        current_char = chr(console.ch[x, y]) if console.ch[x, y] != 0 else " "
                        current_fg = tuple(console.fg[x, y])
                        console.print(x, y, current_char, fg=current_fg, bg=highlight_color)
        elif self.selection_mode == "selecting_enemy":
            # Highlight enemy side
            highlight_color = (150, 100, 255)
            for dy in range(grid_height):
                for dx in range(ENCOUNTER_GRID_WIDTH, grid_width):
                    x = grid_start_x + dx
                    y = grid_start_y + dy + 1
                    # Bounds check before accessing console arrays
                    if is_within_console_bounds(x, y):
                        # Get current character and preserve it while changing background
                        current_char = chr(console.ch[x, y]) if console.ch[x, y] != 0 else " "
                        current_fg = tuple(console.fg[x, y])
                        console.print(x, y, current_char, fg=current_fg, bg=highlight_color)

        # BOTTOM RIGHT: Actions panel
        actions_start_y = top_panel_height + 2
        console.print(right_panel_x + 2, actions_start_y, "ACTIONS", fg=(255, 255, 0))
        
        if self.action_mode in ("attack", "convert"):
            # Show target selection instructions
            action_name = "ATTACK" if self.action_mode == "attack" else "CONVERT"
            console.print(right_panel_x + 2, actions_start_y + 2, f"Select {action_name} target:", fg=(255, 255, 100))
            console.print(right_panel_x + 2, actions_start_y + 3, "Use numpad 1-9", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 4, "ESC to cancel", fg=(150, 150, 150))
        elif self.selection_mode in ("selecting_ally", "selecting_enemy"):
            # Show selection instructions
            side_name = "ALLY" if self.selection_mode == "selecting_ally" else "ENEMY"
            console.print(right_panel_x + 2, actions_start_y + 2, f"Select {side_name}:", fg=(255, 255, 100))
            console.print(right_panel_x + 2, actions_start_y + 3, "Use numpad 1-9", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 4, "ESC to cancel", fg=(150, 150, 150))
        else:
            # Show available actions
            console.print(right_panel_x + 2, actions_start_y + 2, "[A] Attack", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 3, "[C] Convert", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 4, "[Q] Select Ally", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 5, "[E] Select Enemy", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 6, "[F] Flee", fg=(200, 200, 200))


class MainMenu(Screen):
    """Main menu screen with options for New Game, Options, and Exit."""

    def __init__(self):
        """Initialize the MainMenu screen."""
        self.options = ["New Game", "Options", "Exit"]
        self.selected_index = 0

    def handle_specific_event(self, event: tcod.event.Event, game: "game.Game") -> None:
        """Handle main menu-specific input events.

        Allows navigation through menu options with UP/DOWN or numpad 8/2,
        and selection with Enter key.

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

    def _select_option(self, game: "game.Game") -> None:
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

    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the main menu to the console.

        Args:
            console: The console to render to
            game: The game instance
        """

        console.clear()

        # Draw title
        title = "MAIN MENU"
        title_x = (GRID_WIDTH - len(title)) // 2
        console.print(title_x, GRID_HEIGHT // 4, title, fg=(255, 255, 0))

        # Draw menu options
        start_y = GRID_HEIGHT // 2
        for i, option in enumerate(self.options):
            y = start_y + i * 2
            x = (GRID_WIDTH - len(option) - 4) // 2

            if i == self.selected_index:
                # Highlight selected option
                console.print(x, y, f"> {option} <", fg=(0, 255, 0))
            else:
                console.print(x + 2, y, option, fg=(200, 200, 200))

        # Draw instructions
        instructions = "Use UP/DOWN or numpad 8/2 to navigate."
        instr_x = (GRID_WIDTH - len(instructions)) // 2
        console.print(instr_x, GRID_HEIGHT - 3, instructions, fg=(150, 150, 150))
        instructions_two = "ENTER to select. ESC to quit."
        instr_x_two = (GRID_WIDTH - len(instructions_two)) // 2
        console.print(instr_x_two, GRID_HEIGHT - 2, instructions_two, fg=(150, 150, 150))
