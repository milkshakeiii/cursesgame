#!/usr/bin/env python3
"""Screen classes for the game."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

import tcod

from game_data import GRID_HEIGHT, GRID_WIDTH, Player, Creature
from gameplay import advance_step

if TYPE_CHECKING:
    import game

# Constants for encounter grid
ENCOUNTER_GRID_WIDTH = 3  # 3x3 grid for each side
ENCOUNTER_GRID_HEIGHT = 3


class EncounterMode(Enum):
    """Enum for encounter screen modes."""
    NORMAL = "normal"
    ATTACK = "attack"
    CONVERT = "convert"
    SELECTING_ALLY = "selecting_ally"
    SELECTING_ENEMY = "selecting_enemy"


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
        self.mode = EncounterMode.NORMAL  # Current interaction mode
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
            if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
                if event.sym in self.target_selection_map:
                    # Get the target coordinates
                    target_x, target_y = self.target_selection_map[event.sym]
                    
                    # Execute the action through advance_step
                    action_type = "attack" if self.mode == EncounterMode.ATTACK else "convert"
                    game.gamestate = advance_step(game.gamestate, (action_type, target_x, target_y))
                    
                    # Exit selection mode
                    self.mode = EncounterMode.NORMAL
                    
                    # Check if encounter ended (all creatures defeated or converted)
                    if game.gamestate.active_encounter is None:
                        game.current_back_screen = game.map_view
                elif event.sym == tcod.event.KeySym.ESCAPE:
                    # Cancel target selection
                    self.mode = EncounterMode.NORMAL
            # If in ally/enemy selection mode, handle numpad input
            elif self.mode in (EncounterMode.SELECTING_ALLY, EncounterMode.SELECTING_ENEMY):
                if event.sym in self.target_selection_map:
                    # Get the grid position
                    grid_x, grid_y = self.target_selection_map[event.sym]
                    grid_index = grid_y * ENCOUNTER_GRID_WIDTH + grid_x
                    
                    # Update selection
                    if self.mode == EncounterMode.SELECTING_ALLY:
                        self.selected_side = "player"
                    else:
                        self.selected_side = "enemy"
                    self.selected_index = grid_index
                    
                    # Exit selection mode
                    self.mode = EncounterMode.NORMAL
                elif event.sym == tcod.event.KeySym.ESCAPE:
                    # Cancel selection
                    self.mode = EncounterMode.NORMAL
            else:
                # Normal mode - handle action/selection keys
                if event.sym == tcod.event.KeySym.A:
                    # Enter attack target selection mode (only enemies)
                    self.mode = EncounterMode.ATTACK
                elif event.sym == tcod.event.KeySym.C:
                    # Enter convert target selection mode (only enemies)
                    self.mode = EncounterMode.CONVERT
                elif event.sym == tcod.event.KeySym.Q:
                    # Enter ally selection mode
                    self.mode = EncounterMode.SELECTING_ALLY
                elif event.sym == tcod.event.KeySym.E:
                    # Enter enemy selection mode
                    self.mode = EncounterMode.SELECTING_ENEMY
                elif event.sym == tcod.event.KeySym.F:
                    # Flee - return to map
                    game.gamestate.active_encounter = None
                    game.current_back_screen = game.map_view

    def _get_selected_entity(self, game: "game.Game") -> Optional[Union[Creature, Player]]:
        """Get the currently selected entity.
        
        Args:
            game: The game instance
        
        Returns:
            The selected Creature or Player, or None if no entity is selected
        """
        if game.gamestate.active_encounter is None:
            return None
            
        if self.selected_side == "player":
            team = game.gamestate.active_encounter.player_team
            if team and self.selected_index < len(team):
                return team[self.selected_index]
        else:  # enemy side
            team = game.gamestate.active_encounter.enemy_team
            if team and self.selected_index < len(team):
                return team[self.selected_index]
        
        return None

    def _render_dividers(self, console: tcod.console.Console, info_panel_width: int, 
                        right_panel_x: int, top_panel_height: int) -> None:
        """Render the divider lines separating panels.
        
        Args:
            console: The console to render to
            info_panel_width: X position of the vertical divider
            right_panel_x: X position where right panel starts
            top_panel_height: Y position of the horizontal divider
        """
        # Draw vertical divider between left and right
        for y in range(GRID_HEIGHT):
            console.print(info_panel_width, y, "|", fg=(100, 100, 100))

        # Draw horizontal divider in right panel
        for x in range(right_panel_x + 1, GRID_WIDTH):
            console.print(x, top_panel_height, "-", fg=(100, 100, 100))

    def _render_info_panel(self, console: tcod.console.Console, game: "game.Game", 
                          selected_entity: Optional[Union[Creature, Player]]) -> None:
        """Render the information panel showing selected entity stats.
        
        Args:
            console: The console to render to
            game: The game instance
            selected_entity: The selected Creature or Player, or None
        """
        console.print(2, 1, "BATTLE INFO", fg=(255, 255, 0))
        
        if isinstance(selected_entity, Creature):
            side_label = "Ally" if self.selected_side == "player" else "Enemy"
            console.print(2, 3, f"{side_label}: {selected_entity.name}", fg=(200, 200, 200))
            health_color = (0, 255, 0) if selected_entity.current_health > 30 else (255, 100, 100)
            console.print(2, 4, f"HP: {selected_entity.current_health}/{selected_entity.max_health}", fg=health_color)
            console.print(2, 5, f"Convert: {selected_entity.current_convert}/100", fg=(150, 150, 255))
        elif isinstance(selected_entity, Player):
            console.print(2, 3, f"Player", fg=(200, 200, 200))
            health_color = (0, 255, 0) if selected_entity.current_health > 30 else (255, 100, 100)
            console.print(2, 4, f"HP: {selected_entity.current_health}/{selected_entity.max_health}", fg=health_color)
        else:
            console.print(2, 3, "No selection", fg=(200, 200, 200))

    def _render_battle_grid_border(self, console: tcod.console.Console, grid_start_x: int, 
                                   grid_start_y: int, grid_width: int, grid_height: int) -> None:
        """Render the border and corners of the battle grid.
        
        Args:
            console: The console to render to
            grid_start_x: X position where grid starts
            grid_start_y: Y position where grid starts
            grid_width: Width of the battle grid
            grid_height: Height of the battle grid
        """
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
        console.print(grid_start_x + grid_width, grid_start_y + grid_height + 1, "+", fg=(100, 100, 100))

    def _render_team_entities(self, console: tcod.console.Console, team: list, 
                             grid_start_x: int, grid_start_y: int, x_offset: int, 
                             is_player_team: bool) -> None:
        """Render entities from a team on the battle grid.
        
        Args:
            console: The console to render to
            team: List of entities (Player or Creature) to render
            grid_start_x: X position where grid starts
            grid_start_y: Y position where grid starts
            x_offset: Horizontal offset for positioning (0 for player team, 3 for enemy team)
            is_player_team: True if rendering player team, False for enemy team
        """
        if not team:
            return
            
        for i in range(9):
            grid_x = i % 3
            grid_y = i // 3
            screen_x = grid_start_x + x_offset + grid_x
            screen_y = grid_start_y + 1 + grid_y
            
            entity = team[i]
            if entity:
                # Determine symbol and color
                if isinstance(entity, Player):
                    symbol = "@"
                    color = (0, 255, 0)
                else:
                    symbol = entity.symbol
                    color = entity.color
                
                # Check if this is the selected entity
                side_matches = (is_player_team and self.selected_side == "player") or \
                              (not is_player_team and self.selected_side == "enemy")
                is_selected = side_matches and self.selected_index == i
                bg_color = (100, 100, 50) if is_selected else (0, 0, 0)
                
                console.print(screen_x, screen_y, symbol, fg=color, bg=bg_color)

    def _apply_grid_highlighting(self, console: tcod.console.Console, grid_start_x: int, 
                                 grid_start_y: int, grid_width: int, grid_height: int) -> None:
        """Apply highlighting to the battle grid based on current mode.
        
        Args:
            console: The console to render to
            grid_start_x: X position where grid starts
            grid_start_y: Y position where grid starts
            grid_width: Width of the battle grid
            grid_height: Height of the battle grid
        """
        if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
            # Highlight enemy side for attack/convert
            highlight_color = (255, 255, 100) if self.mode == EncounterMode.ATTACK else (150, 150, 255)
            self._highlight_grid_region(console, grid_start_x, grid_start_y, grid_height,
                                       ENCOUNTER_GRID_WIDTH, grid_width, highlight_color)
        elif self.mode == EncounterMode.SELECTING_ALLY:
            # Highlight player side
            highlight_color = (100, 150, 255)
            self._highlight_grid_region(console, grid_start_x, grid_start_y, grid_height,
                                       0, ENCOUNTER_GRID_WIDTH, highlight_color)
        elif self.mode == EncounterMode.SELECTING_ENEMY:
            # Highlight enemy side
            highlight_color = (150, 100, 255)
            self._highlight_grid_region(console, grid_start_x, grid_start_y, grid_height,
                                       ENCOUNTER_GRID_WIDTH, grid_width, highlight_color)

    def _highlight_grid_region(self, console: tcod.console.Console, grid_start_x: int, 
                               grid_start_y: int, grid_height: int,
                               dx_start: int, dx_end: int, highlight_color: tuple[int, int, int]) -> None:
        """Apply highlighting to a specific region of the battle grid.
        
        Args:
            console: The console to render to
            grid_start_x: X position where grid starts
            grid_start_y: Y position where grid starts
            grid_height: Height of the battle grid
            dx_start: Starting X offset for the region to highlight
            dx_end: Ending X offset for the region to highlight
            highlight_color: RGB color tuple for the highlight
        """
        for dy in range(grid_height):
            for dx in range(dx_start, dx_end):
                x = grid_start_x + dx
                y = grid_start_y + dy + 1
                # Bounds check before accessing console arrays
                if is_within_console_bounds(x, y):
                    # Get current character and preserve it while changing background
                    current_char = chr(console.ch[x, y]) if console.ch[x, y] != 0 else " "
                    current_fg = tuple(console.fg[x, y])
                    console.print(x, y, current_char, fg=current_fg, bg=highlight_color)

    def _render_actions_panel(self, console: tcod.console.Console, right_panel_x: int, 
                             actions_start_y: int) -> None:
        """Render the actions panel showing available commands.
        
        Args:
            console: The console to render to
            right_panel_x: X position where right panel starts
            actions_start_y: Y position where actions panel starts
        """
        console.print(right_panel_x + 2, actions_start_y, "ACTIONS", fg=(255, 255, 0))
        
        if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
            # Show target selection instructions
            action_name = "ATTACK" if self.mode == EncounterMode.ATTACK else "CONVERT"
            console.print(right_panel_x + 2, actions_start_y + 2, f"Select {action_name} target:", fg=(255, 255, 100))
            console.print(right_panel_x + 2, actions_start_y + 3, "Use numpad 1-9", fg=(200, 200, 200))
            console.print(right_panel_x + 2, actions_start_y + 4, "ESC to cancel", fg=(150, 150, 150))
        elif self.mode in (EncounterMode.SELECTING_ALLY, EncounterMode.SELECTING_ENEMY):
            # Show selection instructions
            side_name = "ALLY" if self.mode == EncounterMode.SELECTING_ALLY else "ENEMY"
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

    def render(self, console: tcod.console.Console, game: "game.Game") -> None:
        """Render the encounter screen to the console.

        Args:
            console: The console to render to
            game: The game instance
        """
        # Sanity check - we should never be rendering this screen without an active encounter
        assert game.gamestate.active_encounter is not None, \
            "EncounterScreen.render called without active encounter"
        
        console.clear()

        # Calculate layout dimensions
        info_panel_width = GRID_WIDTH // 2
        right_panel_x = info_panel_width
        right_panel_width = GRID_WIDTH - info_panel_width
        top_panel_height = GRID_HEIGHT // 2

        # Render dividers
        self._render_dividers(console, info_panel_width, right_panel_x, top_panel_height)

        # Get selected entity
        selected_entity = self._get_selected_entity(game)

        # Render info panel
        self._render_info_panel(console, game, selected_entity)

        # Calculate battle grid dimensions
        grid_width = 6
        grid_height = 3
        grid_start_x = right_panel_x + (right_panel_width - grid_width) // 2
        grid_start_y = 2

        # Render battle grid border
        self._render_battle_grid_border(console, grid_start_x, grid_start_y, grid_width, grid_height)

        # Render entities from both teams
        player_team = game.gamestate.active_encounter.player_team
        enemy_team = game.gamestate.active_encounter.enemy_team
        
        self._render_team_entities(console, player_team, grid_start_x, grid_start_y, 0, True)
        self._render_team_entities(console, enemy_team, grid_start_x, grid_start_y, 3, False)

        # Apply highlighting based on current mode
        self._apply_grid_highlighting(console, grid_start_x, grid_start_y, grid_width, grid_height)

        # Render actions panel
        actions_start_y = top_panel_height + 2
        self._render_actions_panel(console, right_panel_x, actions_start_y)


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
