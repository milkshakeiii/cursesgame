import pygame
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Union
from enum import Enum

from game_data import GRID_HEIGHT, GRID_WIDTH, LEFT_PANEL_WIDTH, Player, Creature
from gameplay import advance_step, select_best_attack, calculate_expected_result
from combat import get_hero_attacks

if TYPE_CHECKING:
    import game as game_module

# Constants for encounter grid
ENCOUNTER_GRID_WIDTH = 3
ENCOUNTER_GRID_HEIGHT = 3

class EncounterMode(Enum):
    """Enum for encounter screen modes."""
    NORMAL = "normal"
    ATTACK = "attack"
    CONVERT = "convert"
    MOVE = "move"  # Move a unit
    SELECTING_ALLY = "selecting_ally"
    SELECTING_ENEMY = "selecting_enemy"
    SELECTING_MOVE_SOURCE = "selecting_move_source"  # Select unit to move
    SELECTING_MOVE_TARGET = "selecting_move_target"  # Select destination

class Screen(ABC):
    """Base class for screens in the game."""

    def handle_event(self, event: pygame.event.Event, game: "game_module.Game") -> None:
        """Handle an input event."""
        if event.type == pygame.QUIT:
            game.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_ALT):
                game.toggle_fullscreen()
            elif event.key == pygame.K_ESCAPE:
                if not self.handle_specific_event(event, game):
                    # Show exit confirmation popup instead of quitting directly
                    game.current_front_screen = game.exit_confirmation_screen
            else:
                self.handle_specific_event(event, game)
        else:
            self.handle_specific_event(event, game)

    @abstractmethod
    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        """
        Handle a screen-specific input event.
        Returns True if the event was consumed, False if default handling (like quitting) should occur.
        """
        return False

    @abstractmethod
    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        """Render the screen to the display."""
        pass

    def draw_text(self, screen: pygame.Surface, text: str, x: int, y: int, color: tuple[int, int, int], font: pygame.font.Font, centered: bool = False):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if centered:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        screen.blit(surface, rect)

    def get_panel_width_pixels(self, game: "game_module.Game") -> int:
        """Get the width of the left panel in pixels."""
        return LEFT_PANEL_WIDTH * game.sprite_manager.tile_width

    def draw_left_panel(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        """Draw the left panel background with a border."""
        panel_width = self.get_panel_width_pixels(game)
        # Dark panel background
        pygame.draw.rect(screen, (20, 20, 30), (0, 0, panel_width, screen.get_height()))
        # Border line
        pygame.draw.line(screen, (60, 60, 80), (panel_width - 1, 0), (panel_width - 1, screen.get_height()))

    def get_map_area_center_x(self, screen: pygame.Surface, game: "game_module.Game") -> int:
        """Get the center x coordinate of the map area (excluding left panel)."""
        panel_width = self.get_panel_width_pixels(game)
        map_area_width = screen.get_width() - panel_width
        return panel_width + map_area_width // 2


class ExitConfirmationScreen(Screen):
    """Popup screen for exit confirmation."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_event(self, event: pygame.event.Event, game: "game_module.Game") -> None:
        """Override to prevent escape from showing another popup."""
        if event.type == pygame.QUIT:
            game.running = False
        elif event.type == pygame.KEYDOWN:
            self.handle_specific_event(event, game)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                game.running = False
                return True
            elif event.key == pygame.K_m:
                game.current_front_screen = None
                game.current_back_screen = game.main_menu
                return True
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                game.current_front_screen = None
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        # Draw semi-transparent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Draw confirmation box
        box_width, box_height = 300, 120
        box_x = (screen.get_width() - box_width) // 2
        box_y = (screen.get_height() - box_height) // 2

        pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (150, 150, 150), (box_x, box_y, box_width, box_height), 2)

        center_x = screen.get_width() // 2
        self.draw_text(screen, "Quit game?", center_x, box_y + 30, (255, 255, 255), self.font, centered=True)
        self.draw_text(screen, "(Y)es  /  (N)o", center_x, box_y + 60, (200, 200, 200), self.small_font, centered=True)
        self.draw_text(screen, "(M)ain Menu", center_x, box_y + 85, (200, 200, 200), self.small_font, centered=True)


class BiomeOrderScreen(Screen):
    """Screen shown before a new run to display biome order."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                game.current_back_screen = game.map_view
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # No left panel on journey preview
        center_x = screen.get_width() // 2
        self.draw_text(screen, "UPCOMING JOURNEY", center_x, 50, (255, 255, 0), self.font, centered=True)

        if game.gamestate.biome_order:
            for i, biome in enumerate(game.gamestate.biome_order):
                y_pos = 150 + i * 50
                levels = f"Levels {i*5+1}-{i*5+5}"
                biome_name = biome.replace("_", " ").title()

                # Biome color mapping for flair
                color = (200, 200, 200)
                if biome == "forest": color = (34, 139, 34)
                elif biome == "plains": color = (218, 165, 32)
                elif biome == "snow": color = (200, 240, 255)
                elif biome == "underground": color = (100, 100, 100)

                self.draw_text(screen, f"{levels}: {biome_name}", center_x, y_pos, color, self.small_font, centered=True)

        self.draw_text(screen, "Press ENTER to begin", center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)


class TeamArrangementScreen(Screen):
    """Screen for rearranging the player's team."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 14)
        self.header_font = pygame.font.SysFont("monospace", 18, bold=True)
        self.selected_area = "grid" # "grid" or "pending"
        self.selected_index = 4 # Default to center
        self.swap_source = None # (area, index)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            # --- SELECTION & MOVEMENT ---
            nav_keys = (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                        pygame.K_KP4, pygame.K_KP6, pygame.K_KP8, pygame.K_KP2,
                        pygame.K_KP7, pygame.K_KP9, pygame.K_KP1, pygame.K_KP3,
                        pygame.K_j, pygame.K_l, pygame.K_i, pygame.K_COMMA,
                        pygame.K_u, pygame.K_o, pygame.K_m, pygame.K_PERIOD)
            if event.key in nav_keys:
                if self.selected_area == "grid":
                    col = self.selected_index % 3
                    row = self.selected_index // 3

                    if event.key in (pygame.K_LEFT, pygame.K_KP4, pygame.K_j): col = (col - 1) % 3
                    elif event.key in (pygame.K_RIGHT, pygame.K_KP6, pygame.K_l): col = (col + 1) % 3
                    elif event.key in (pygame.K_UP, pygame.K_KP8, pygame.K_i): row = (row - 1) % 3
                    elif event.key in (pygame.K_DOWN, pygame.K_KP2, pygame.K_COMMA):
                        row = (row + 1) % 3
                        if row == 0 and self.selected_index // 3 == 2 and game.gamestate.pending_recruits:
                            self.selected_area = "pending"
                            self.selected_index = 0
                            return True

                    # Diagonals
                    elif event.key in (pygame.K_KP7, pygame.K_u): # Up-Left
                        col = (col - 1) % 3
                        row = (row - 1) % 3
                    elif event.key in (pygame.K_KP9, pygame.K_o): # Up-Right
                        col = (col + 1) % 3
                        row = (row - 1) % 3
                    elif event.key in (pygame.K_KP1, pygame.K_m): # Down-Left
                        col = (col - 1) % 3
                        row = (row + 1) % 3
                        if row == 0 and self.selected_index // 3 == 2 and game.gamestate.pending_recruits:
                            self.selected_area = "pending"
                            self.selected_index = 0
                            return True
                    elif event.key in (pygame.K_KP3, pygame.K_PERIOD): # Down-Right
                        col = (col + 1) % 3
                        row = (row + 1) % 3
                        if row == 0 and self.selected_index // 3 == 2 and game.gamestate.pending_recruits:
                            self.selected_area = "pending"
                            self.selected_index = 0
                            return True

                    self.selected_index = row * 3 + col

                elif self.selected_area == "pending":
                    count = len(game.gamestate.pending_recruits)
                    if count == 0:
                        self.selected_area = "grid"
                        self.selected_index = 7
                        return True

                    if event.key in (pygame.K_LEFT, pygame.K_KP4, pygame.K_j):
                        self.selected_index = (self.selected_index - 1) % count
                    elif event.key in (pygame.K_RIGHT, pygame.K_KP6, pygame.K_l):
                        self.selected_index = (self.selected_index + 1) % count
                    elif event.key in (pygame.K_UP, pygame.K_KP8, pygame.K_KP7, pygame.K_KP9, pygame.K_i, pygame.K_u, pygame.K_o):
                        self.selected_area = "grid"
                        self.selected_index = 7
                return True

            # --- ACTIONS ---
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_k):
                if self.swap_source is None:
                    # Pick up
                    if self.selected_area == "pending":
                        if not game.gamestate.pending_recruits: return True
                    self.swap_source = (self.selected_area, self.selected_index)
                else:
                    # Swap/Place
                    area1, idx1 = self.swap_source
                    area2, idx2 = self.selected_area, self.selected_index
                    
                    player = self._get_player(game)
                    pending = game.gamestate.pending_recruits
                    
                    # 1. Grid <-> Grid
                    if area1 == "grid" and area2 == "grid":
                        unit1 = player.creatures[idx1] if idx1 != player.team_position else None
                        unit2 = player.creatures[idx2] if idx2 != player.team_position else None
                        size1 = getattr(unit1, "size", "1x1") if unit1 else "1x1"
                        size2 = getattr(unit2, "size", "1x1") if unit2 else "1x1"

                        # 2x2 unit movement within grid
                        if size1 == "2x2":
                            # Find top-left of the 2x2 unit
                            top_left = None
                            for i, c in enumerate(player.creatures):
                                if c is unit1:
                                    if top_left is None or i < top_left:
                                        top_left = i
                            tl_row, tl_col = top_left // 3, top_left % 3

                            # Calculate delta from source to target
                            src_row, src_col = idx1 // 3, idx1 % 3
                            tgt_row, tgt_col = idx2 // 3, idx2 % 3
                            dr, dc = tgt_row - src_row, tgt_col - src_col

                            # Only allow orthogonal 1-step moves
                            if not ((abs(dr) == 1 and dc == 0) or (dr == 0 and abs(dc) == 1)):
                                self.swap_source = None
                                return True

                            # Calculate new top-left position
                            new_tl_row, new_tl_col = tl_row + dr, tl_col + dc

                            # Check bounds (2x2 must fit in grid)
                            if new_tl_row < 0 or new_tl_row > 1 or new_tl_col < 0 or new_tl_col > 1:
                                self.swap_source = None
                                return True

                            # Old and new positions
                            old_positions = [
                                tl_row * 3 + tl_col,
                                tl_row * 3 + tl_col + 1,
                                (tl_row + 1) * 3 + tl_col,
                                (tl_row + 1) * 3 + tl_col + 1,
                            ]
                            new_positions = [
                                new_tl_row * 3 + new_tl_col,
                                new_tl_row * 3 + new_tl_col + 1,
                                (new_tl_row + 1) * 3 + new_tl_col,
                                (new_tl_row + 1) * 3 + new_tl_col + 1,
                            ]

                            # Positions being vacated and newly occupied
                            vacated = [p for p in old_positions if p not in new_positions]
                            newly_occupied = [p for p in new_positions if p not in old_positions]

                            # Check if player needs to be displaced
                            player_displaced = player.team_position in newly_occupied

                            # Collect displaced units from newly occupied positions
                            displaced = []
                            for pos in newly_occupied:
                                other = player.creatures[pos]
                                if other is not None and other is not unit1:
                                    displaced.append(other)

                            # Clear old positions
                            for pos in old_positions:
                                player.creatures[pos] = None

                            # Place 2x2 in new positions
                            for pos in new_positions:
                                player.creatures[pos] = unit1

                            # Place displaced units in vacated positions
                            vacated_idx = 0
                            if player_displaced:
                                # Move player to first vacated position
                                player.team_position = vacated[vacated_idx]
                                vacated_idx += 1

                            for unit in displaced:
                                if vacated_idx < len(vacated):
                                    player.creatures[vacated[vacated_idx]] = unit
                                    vacated_idx += 1
                                else:
                                    pending.append(unit)

                        elif size2 == "2x2":
                            # Can't swap onto a 2x2 from a 1x1; user should select the 2x2 to move it
                            self.swap_source = None
                            return True

                        # Handle player position swaps
                        elif idx1 == player.team_position:
                            # Moving player to idx2, move creature at idx2 to idx1
                            player.creatures[idx1] = player.creatures[idx2]
                            player.creatures[idx2] = None
                            player.team_position = idx2
                        elif idx2 == player.team_position:
                            # Moving player to idx1, move creature at idx1 to idx2
                            player.creatures[idx2] = player.creatures[idx1]
                            player.creatures[idx1] = None
                            player.team_position = idx1
                        else:
                            # Normal creature swap
                            player.creatures[idx1], player.creatures[idx2] = player.creatures[idx2], player.creatures[idx1]
                    
                    # 2. Pending -> Grid
                    elif area1 == "pending" and area2 == "grid":
                        recruit = pending[idx1]
                        recruit_size = getattr(recruit, "size", "1x1")

                        if recruit_size == "2x2":
                            # 2x2 placement: idx2 becomes top-left of 2x2 footprint
                            top_left_row = idx2 // 3
                            top_left_col = idx2 % 3

                            # Check if 2x2 fits (must not exceed grid bounds)
                            if top_left_row > 1 or top_left_col > 1:
                                # Can't place - would extend beyond grid
                                self.swap_source = None
                                return True

                            # Calculate all 4 positions
                            positions = [
                                top_left_row * 3 + top_left_col,      # top-left
                                top_left_row * 3 + top_left_col + 1,  # top-right
                                (top_left_row + 1) * 3 + top_left_col,      # bottom-left
                                (top_left_row + 1) * 3 + top_left_col + 1,  # bottom-right
                            ]

                            # Check if player is in any of these positions
                            if player.team_position in positions:
                                self.swap_source = None
                                return True

                            # Collect displaced units
                            displaced = []
                            for pos in positions:
                                existing = player.creatures[pos]
                                if existing is not None:
                                    # Don't add duplicates (in case of existing 2x2)
                                    if existing not in displaced:
                                        displaced.append(existing)
                                    player.creatures[pos] = None

                            # Place 2x2 unit in all 4 positions
                            for pos in positions:
                                player.creatures[pos] = recruit

                            # Remove recruit from pending and add displaced units
                            pending.pop(idx1)
                            for d in displaced:
                                pending.append(d)

                            if self.selected_area == "pending" and self.selected_index >= len(pending):
                                self.selected_index = max(0, len(pending) - 1)
                        else:
                            # 1x1 placement (original logic)
                            # Can't place recruit on player's position
                            if idx2 == player.team_position:
                                self.swap_source = None
                                return True

                            existing = player.creatures[idx2]

                            player.creatures[idx2] = recruit
                            if existing:
                                pending[idx1] = existing
                            else:
                                pending.pop(idx1)
                                if self.selected_area == "pending" and self.selected_index >= len(pending):
                                    self.selected_index = max(0, len(pending) - 1)
                    
                    # 3. Grid -> Pending
                    elif area1 == "grid" and area2 == "pending":
                        # Can't move player to pending
                        if idx1 == player.team_position:
                            self.swap_source = None
                            return True

                        existing = player.creatures[idx1]
                        recruit = pending[idx2]
                        recruit_size = getattr(recruit, "size", "1x1")

                        if existing:
                            existing_size = getattr(existing, "size", "1x1")

                            if existing_size == "2x2":
                                # Remove 2x2 from all positions
                                for i, c in enumerate(player.creatures):
                                    if c is existing:
                                        player.creatures[i] = None

                            # Now place the recruit
                            if recruit_size == "2x2":
                                # Use idx1 as top-left for 2x2 placement
                                top_left_row = idx1 // 3
                                top_left_col = idx1 % 3

                                if top_left_row > 1 or top_left_col > 1:
                                    # Can't place 2x2 here - restore and cancel
                                    if existing_size == "2x2":
                                        # Need to restore the 2x2 - find its original positions
                                        # For now, just add back to pending
                                        pending.append(existing)
                                    else:
                                        player.creatures[idx1] = existing
                                    self.swap_source = None
                                    return True

                                positions = [
                                    top_left_row * 3 + top_left_col,
                                    top_left_row * 3 + top_left_col + 1,
                                    (top_left_row + 1) * 3 + top_left_col,
                                    (top_left_row + 1) * 3 + top_left_col + 1,
                                ]

                                if player.team_position in positions:
                                    # Restore and cancel
                                    if existing_size == "2x2":
                                        pending.append(existing)
                                    else:
                                        player.creatures[idx1] = existing
                                    self.swap_source = None
                                    return True

                                # Collect any additional displaced units (not the original existing)
                                for pos in positions:
                                    other = player.creatures[pos]
                                    if other is not None and other is not existing:
                                        if other not in pending:
                                            pending.append(other)
                                        player.creatures[pos] = None

                                # Place 2x2 recruit
                                for pos in positions:
                                    player.creatures[pos] = recruit
                                pending[idx2] = existing
                            else:
                                # 1x1 recruit placement
                                player.creatures[idx1] = recruit
                                pending[idx2] = existing
                        else:
                            # Grid is empty, just place the recruit
                            if recruit_size == "2x2":
                                top_left_row = idx1 // 3
                                top_left_col = idx1 % 3

                                if top_left_row > 1 or top_left_col > 1:
                                    self.swap_source = None
                                    return True

                                positions = [
                                    top_left_row * 3 + top_left_col,
                                    top_left_row * 3 + top_left_col + 1,
                                    (top_left_row + 1) * 3 + top_left_col,
                                    (top_left_row + 1) * 3 + top_left_col + 1,
                                ]

                                if player.team_position in positions:
                                    self.swap_source = None
                                    return True

                                # Collect displaced units
                                for pos in positions:
                                    other = player.creatures[pos]
                                    if other is not None:
                                        if other not in pending:
                                            pending.append(other)
                                        player.creatures[pos] = None

                                for pos in positions:
                                    player.creatures[pos] = recruit
                                pending.pop(idx2)
                            else:
                                player.creatures[idx1] = recruit
                                pending.pop(idx2)
                            self.selected_area = "grid"
                            self.selected_index = idx1
                    
                    # 4. Pending <-> Pending
                    elif area1 == "pending" and area2 == "pending":
                        pending[idx1], pending[idx2] = pending[idx2], pending[idx1]

                    self.swap_source = None
                return True

            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                if self.selected_area == "grid":
                    player = self._get_player(game)

                    # Can't delete the player
                    if self.selected_index == player.team_position:
                        return True

                    existing = player.creatures[self.selected_index]
                    if existing:
                        existing_size = getattr(existing, "size", "1x1")
                        if existing_size == "2x2":
                            # Clear all 4 positions of the 2x2 unit
                            for i, c in enumerate(player.creatures):
                                if c is existing:
                                    player.creatures[i] = None
                        else:
                            player.creatures[self.selected_index] = None

                    if self.swap_source == ("grid", self.selected_index):
                        self.swap_source = None

                elif self.selected_area == "pending":
                    if game.gamestate.pending_recruits:
                        game.gamestate.pending_recruits.pop(self.selected_index)
                        if self.selected_index >= len(game.gamestate.pending_recruits):
                            self.selected_index = max(0, len(game.gamestate.pending_recruits) - 1)
                        if self.swap_source == ("pending", self.selected_index):
                             self.swap_source = None
                return True

            elif event.key == pygame.K_ESCAPE:
                if self.swap_source is not None:
                    self.swap_source = None
                else:
                    game.gamestate.pending_recruits = []
                    game.current_back_screen = game.map_view
                return True
        return False

    def _get_player(self, game):
        for p in game.gamestate.placeables:
            if isinstance(p, Player): return p
        return None

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)

        center_x = self.get_map_area_center_x(screen, game)
        center_y = screen.get_height() // 2

        self.draw_text(screen, "TEAM ARRANGEMENT", center_x, 30, (255, 255, 0), self.header_font, centered=True)
        self.draw_text(screen, "Enter: Swap | Del: Dismiss | ESC: Done", center_x, screen.get_height() - 30, (150, 150, 150), self.font, centered=True)

        player = self._get_player(game)
        if not player: return

        # --- GRID RENDER ---
        tile_w = game.sprite_manager.tile_width * 2
        tile_h = game.sprite_manager.tile_height * 2
        grid_start_x = center_x - (1.5 * tile_w)
        grid_start_y = center_y - (2.0 * tile_h)

        # Track rendered 2x2 units to avoid double-rendering
        rendered_2x2 = set()

        for i in range(9):
            grid_x = i % 3
            grid_y = i // 3
            x = grid_start_x + grid_x * tile_w
            y = grid_start_y + grid_y * tile_h

            pygame.draw.rect(screen, (50, 50, 50), (x, y, tile_w, tile_h), 1)

            # Show player at their team_position, creatures elsewhere
            if i == player.team_position:
                creature = player
            else:
                creature = player.creatures[i]

            if self.selected_area == "grid" and i == self.selected_index:
                pygame.draw.rect(screen, (255, 255, 0), (x, y, tile_w, tile_h), 2)

            if self.swap_source == ("grid", i):
                pygame.draw.rect(screen, (0, 255, 0), (x+4, y+4, tile_w-8, tile_h-8), 2)

            if creature:
                size = getattr(creature, "size", "1x1")

                if size == "2x2":
                    # Skip if already rendered
                    if id(creature) in rendered_2x2:
                        continue
                    rendered_2x2.add(id(creature))

                    # Find top-left position of this 2x2 unit
                    positions = [idx for idx, c in enumerate(player.creatures) if c is creature]
                    if positions:
                        min_pos = min(positions)
                        top_left_row = min_pos // 3
                        top_left_col = min_pos % 3
                        top_left_x = grid_start_x + top_left_col * tile_w
                        top_left_y = grid_start_y + top_left_row * tile_h

                        # Draw 2x2 unit across 4 cells
                        glyphs = getattr(creature, "glyphs", None) or [creature.symbol] * 4
                        for gi, (dx, dy) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
                            glyph = glyphs[gi] if gi < len(glyphs) else creature.symbol
                            sprite = game.sprite_manager.get_sprite(glyph, creature.color)
                            scaled = pygame.transform.scale(sprite, (tile_w, tile_h))
                            screen.blit(scaled, (top_left_x + dx * tile_w, top_left_y + dy * tile_h))

                        # Draw selection highlight across all 4 cells if any is selected
                        if self.selected_area == "grid" and self.selected_index in positions:
                            pygame.draw.rect(screen, (255, 255, 0),
                                (top_left_x, top_left_y, tile_w * 2, tile_h * 2), 2)
                else:
                    sprite = game.sprite_manager.get_sprite(creature.symbol, creature.color)
                    scaled = pygame.transform.scale(sprite, (tile_w, tile_h))
                    screen.blit(scaled, (x, y))

                if self.selected_area == "grid" and i == self.selected_index:
                    tier = getattr(creature, "tier", 0)
                    tier_text = f" (Tier {tier})" if tier > 0 else ""
                    size_text = " [2x2]" if size == "2x2" else ""
                    self.draw_text(screen, f"{creature.name}{tier_text}{size_text}", center_x, grid_start_y + 3 * tile_h + 20, (255, 255, 255), self.font, centered=True)

        # --- PENDING RENDER ---
        pending = game.gamestate.pending_recruits or []
        if pending:
            self.draw_text(screen, "PENDING RECRUITS", center_x, grid_start_y + 3 * tile_h + 50, (100, 200, 255), self.font, centered=True)

            pending_start_x = center_x - (len(pending) * tile_w) // 2
            pending_y = grid_start_y + 3 * tile_h + 80

            for i, creature in enumerate(pending):
                x = pending_start_x + i * tile_w
                y = pending_y

                pygame.draw.rect(screen, (50, 50, 50), (x, y, tile_w, tile_h), 1)

                # Highlight
                if self.selected_area == "pending" and i == self.selected_index:
                    pygame.draw.rect(screen, (255, 255, 0), (x, y, tile_w, tile_h), 2)

                if self.swap_source == ("pending", i):
                    pygame.draw.rect(screen, (0, 255, 0), (x+4, y+4, tile_w-8, tile_h-8), 2)

                # Handle 2x2 units
                size = getattr(creature, "size", "1x1")
                if size == "2x2":
                    glyphs = getattr(creature, "glyphs", None) or [creature.symbol] * 4
                    half_w = tile_w // 2
                    half_h = tile_h // 2
                    for gi, (dx, dy) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
                        glyph = glyphs[gi] if gi < len(glyphs) else creature.symbol
                        sprite = game.sprite_manager.get_sprite(glyph, creature.color)
                        scaled = pygame.transform.scale(sprite, (half_w, half_h))
                        screen.blit(scaled, (x + dx * half_w, y + dy * half_h))
                else:
                    sprite = game.sprite_manager.get_sprite(creature.symbol, creature.color)
                    scaled = pygame.transform.scale(sprite, (tile_w, tile_h))
                    screen.blit(scaled, (x, y))

                if self.selected_area == "pending" and i == self.selected_index:
                    tier = getattr(creature, "tier", 0)
                    tier_text = f" (Tier {tier})" if tier > 0 else ""
                    size_text = " [2x2]" if size == "2x2" else ""
                    self.draw_text(screen, f"{creature.name}{tier_text}{size_text}", center_x, pending_y + tile_h + 20, (200, 200, 255), self.font, centered=True)

class MainMenu(Screen):
    """Main menu screen."""

    def __init__(self):
        self.options = ["New Game", "Options", "Exit"]
        self.selected_index = 0
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_KP8, pygame.K_i):
                self.selected_index = (self.selected_index - 1) % len(self.options)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_KP2, pygame.K_COMMA):
                self.selected_index = (self.selected_index + 1) % len(self.options)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_k):
                self._select_option(game)
                return True
            elif event.key == pygame.K_ESCAPE:
                return False
        return False

    def _select_option(self, game: "game_module.Game") -> None:
        selected = self.options[self.selected_index]
        if selected == "New Game":
            game.reset_game()
            game.current_back_screen = game.biome_order_screen
        elif selected == "Options":
            pass
        elif selected == "Exit":
            game.running = False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw Title (no left panel on main menu)
        title = "MAIN MENU"
        center_x = screen.get_width() // 2
        self.draw_text(screen, title, center_x, screen.get_height() // 4, (255, 255, 0), self.font, centered=True)

        # Draw Options
        start_y = screen.get_height() // 2
        for i, option in enumerate(self.options):
            y = start_y + i * 40
            color = (0, 255, 0) if i == self.selected_index else (200, 200, 200)
            text = f"> {option} <" if i == self.selected_index else option
            self.draw_text(screen, text, center_x, y, color, self.font, centered=True)

        # Draw Instructions
        instr1 = "Use UP/DOWN or numpad 8/2 to navigate."
        instr2 = "ENTER to select. ESC to quit."
        self.draw_text(screen, instr1, center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)
        self.draw_text(screen, instr2, center_x, screen.get_height() - 30, (150, 150, 150), self.small_font, centered=True)


class WinScreen(Screen):
    """Screen shown when the player wins."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 28, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                game.current_back_screen = game.main_menu
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)

        center_x = self.get_map_area_center_x(screen, game)
        self.draw_text(screen, "VICTORY!", center_x, screen.get_height() // 3, (0, 255, 0), self.font, centered=True)
        self.draw_text(screen, "You have defeated the Dragon King!", center_x, screen.get_height() // 2, (200, 255, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER to return to menu", center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)


class GameOverScreen(Screen):
    """Screen shown when the player loses."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 28, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                game.current_back_screen = game.main_menu
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)

        center_x = self.get_map_area_center_x(screen, game)
        self.draw_text(screen, "GAME OVER", center_x, screen.get_height() // 3, (255, 0, 0), self.font, centered=True)
        self.draw_text(screen, "Your journey ends here.", center_x, screen.get_height() // 2, (255, 200, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER to return to menu", center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)


class BattleResultsScreen(Screen):
    """Screen shown after a battle ends to display experience, tier ups, and recruits."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 20, bold=True)
        self.medium_font = pygame.font.SysFont("monospace", 14, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 12)
        self.battle_results = None  # Set when transitioning to this screen
        self.recruits = []  # List of recruited creatures
        self.scroll_offset = 0
        self.max_scroll = 0

    def set_results(self, battle_results: dict, recruits: list):
        """Set the battle results data to display."""
        self.battle_results = battle_results
        self.recruits = recruits or []
        self.scroll_offset = 0
        # Calculate max scroll based on content
        self._calculate_max_scroll()

    def _calculate_max_scroll(self):
        """Calculate maximum scroll offset based on content."""
        if not self.battle_results:
            self.max_scroll = 0
            return

        # Estimate content height
        lines = 0
        lines += 2  # Header
        lines += len(self.battle_results.get("participants", [])) * 2
        lines += 2  # Tier ups header
        for tier_up in self.battle_results.get("tier_ups", []):
            lines += 2 + len(tier_up.get("bonuses", []))
        lines += 2  # Recruits header
        lines += len(self.recruits) * 2

        self.max_scroll = max(0, lines * 20 - 400)  # Rough estimate

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                # Check if player has stat points to allocate
                player = None
                for p in game.gamestate.placeables or []:
                    if isinstance(p, Player):
                        player = p
                        break

                if player and player.stat_points > 0:
                    # Go to stat allocation screen
                    game.current_back_screen = game.stat_allocation_screen
                elif self.recruits:
                    game.current_back_screen = game.team_arrangement_screen
                else:
                    game.current_back_screen = game.map_view
                # Clear results
                self.battle_results = None
                self.recruits = []
                return True
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 30)
                return True
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((20, 20, 30))

        # Draw left panel
        self.draw_left_panel(screen, game)

        panel_width = self.get_panel_width_pixels(game)
        center_x = self.get_map_area_center_x(screen, game)
        height = screen.get_height()

        # Title
        self.draw_text(screen, "BATTLE COMPLETE!", center_x, 30, (100, 255, 100), self.font, centered=True)

        if not self.battle_results:
            self.draw_text(screen, "No battle data available", center_x, height // 2, (150, 150, 150), self.small_font, centered=True)
            self.draw_text(screen, "Press ENTER to continue", center_x, height - 40, (150, 150, 150), self.small_font, centered=True)
            return

        y = 70 - self.scroll_offset
        left_margin = panel_width + 40

        # === EXPERIENCE GAINS ===
        if y > 0 and y < height:
            self.draw_text(screen, "EXPERIENCE GAINED", left_margin, y, (255, 220, 100), self.medium_font)
        y += 28

        participants = self.battle_results.get("participants", [])
        if not participants:
            if y > 0 and y < height:
                self.draw_text(screen, "  No creatures participated", left_margin, y, (150, 150, 150), self.small_font)
            y += 22
        else:
            for p in participants:
                if y > 0 and y < height:
                    name = p["name"]
                    before = p["battles_before"]
                    after = p["battles_after"]
                    self.draw_text(
                        screen,
                        f"  {name}: {before} -> {after} battles (+1)",
                        left_margin, y, (200, 200, 200), self.small_font
                    )
                y += 20

        y += 15

        # === TIER UPS ===
        tier_ups = self.battle_results.get("tier_ups", [])
        if y > 0 and y < height:
            self.draw_text(screen, "TIER UPGRADES", left_margin, y, (255, 180, 50), self.medium_font)
        y += 28

        if not tier_ups:
            if y > 0 and y < height:
                self.draw_text(screen, "  No tier upgrades this battle", left_margin, y, (150, 150, 150), self.small_font)
            y += 22
        else:
            for tier_up in tier_ups:
                name = tier_up["name"]
                old_tier = tier_up["old_tier"]
                new_tier = tier_up["new_tier"]
                bonuses = tier_up.get("bonuses", [])

                if y > 0 and y < height:
                    self.draw_text(
                        screen,
                        f"  {name}: Tier {old_tier} -> Tier {new_tier}!",
                        left_margin, y, (255, 255, 100), self.small_font
                    )
                y += 20

                for bonus in bonuses:
                    if y > 0 and y < height:
                        self.draw_text(
                            screen,
                            f"    + {bonus}",
                            left_margin, y, (150, 255, 150), self.small_font
                        )
                    y += 18

                y += 8

        y += 15

        # === RECRUITS ===
        if y > 0 and y < height:
            self.draw_text(screen, "RECRUITED", left_margin, y, (100, 200, 255), self.medium_font)
        y += 28

        if not self.recruits:
            if y > 0 and y < height:
                self.draw_text(screen, "  No creatures converted", left_margin, y, (150, 150, 150), self.small_font)
            y += 22
        else:
            for creature in self.recruits:
                name = getattr(creature, "name", "Unknown")
                hp = getattr(creature, "max_health", 0)
                efficacy = getattr(creature, "conversion_efficacy", 50)

                if y > 0 and y < height:
                    self.draw_text(
                        screen,
                        f"  {name} - HP: {hp}, Efficacy: {efficacy}%",
                        left_margin, y, (150, 220, 255), self.small_font
                    )
                y += 20

                # Show attacks
                attacks = getattr(creature, "attacks", [])
                for attack in attacks[:2]:  # Limit to 2
                    if y > 0 and y < height:
                        atk_text = f"    {attack.attack_type}: {attack.damage}"
                        if attack.abilities:
                            atk_text += f" [{', '.join(attack.abilities[:2])}]"
                        self.draw_text(screen, atk_text, left_margin, y, (120, 180, 200), self.small_font)
                    y += 18

                y += 8

        # Footer
        footer_y = height - 40
        if self.recruits:
            self.draw_text(
                screen,
                "Press ENTER to place recruits",
                center_x, footer_y, (200, 200, 100), self.small_font, centered=True
            )
        else:
            self.draw_text(
                screen,
                "Press ENTER to continue",
                center_x, footer_y, (150, 150, 150), self.small_font, centered=True
            )

        # Scroll indicators
        if self.scroll_offset > 0:
            self.draw_text(screen, "^ Scroll Up ^", center_x, 55, (100, 100, 100), self.small_font, centered=True)
        if self.scroll_offset < self.max_scroll:
            self.draw_text(screen, "v Scroll Down v", center_x, height - 60, (100, 100, 100), self.small_font, centered=True)


class StatAllocationScreen(Screen):
    """Screen for allocating stat points after completing a floor."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 20, bold=True)
        self.medium_font = pygame.font.SysFont("monospace", 16)
        self.small_font = pygame.font.SysFont("monospace", 12)
        self.selected_stat = 0  # 0=INT, 1=WIS, 2=CHA, 3=BATTLE
        self.stats = ["intelligence", "wisdom", "charisma", "battle"]
        self.stat_names = ["Intelligence", "Wisdom", "Charisma", "Battle"]
        self.stat_descriptions = [
            "Reduces tier requirements, boosts ranged attack/dodge",
            "Buffs ally defenses, boosts melee attack/defense",
            "Increases conversion efficacy, boosts magic attack/resistance",
            "Scales hero combat effectiveness (attacks & defenses)",
        ]

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            player = self._get_player(game)
            if player is None:
                return False

            if event.key in (pygame.K_UP, pygame.K_KP8, pygame.K_i):
                self.selected_stat = (self.selected_stat - 1) % len(self.stats)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_KP2, pygame.K_COMMA):
                self.selected_stat = (self.selected_stat + 1) % len(self.stats)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_k):
                # Allocate a point to selected stat
                if player.stat_points > 0:
                    stat = self.stats[self.selected_stat]
                    setattr(player, stat, getattr(player, stat) + 1)
                    player.stat_points -= 1
                return True
            elif event.key == pygame.K_ESCAPE:
                # Done allocating - check if we need to advance to next floor
                if game.gamestate.pending_next_stage:
                    from gameplay import generate_map
                    game.gamestate.pending_next_stage = False
                    game.gamestate = generate_map(
                        player,
                        game.gamestate.current_stage + 1,
                        game.gamestate.biome_order,
                        game.gamestate.run_seed,
                    )
                    game.current_back_screen = game.map_view
                elif game.gamestate.pending_recruits:
                    game.current_back_screen = game.team_arrangement_screen
                else:
                    game.current_back_screen = game.map_view
                return True
        return False

    def _get_player(self, game: "game_module.Game") -> Optional[Player]:
        for p in game.gamestate.placeables or []:
            if isinstance(p, Player):
                return p
        return None

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((20, 20, 40))

        # Draw left panel
        self.draw_left_panel(screen, game)

        height = screen.get_height()
        center_x = self.get_map_area_center_x(screen, game)

        player = self._get_player(game)
        if player is None:
            return

        # Title
        self.draw_text(screen, "LEVEL COMPLETE!", center_x, 40, (100, 255, 100), self.font, centered=True)

        # Stat points available
        points_color = (255, 255, 100) if player.stat_points > 0 else (150, 150, 150)
        self.draw_text(
            screen,
            f"Stat Points Available: {player.stat_points}",
            center_x, 90, points_color, self.medium_font, centered=True
        )

        # Instructions
        self.draw_text(
            screen,
            "UP/DOWN to select, ENTER to allocate, ESC when done",
            center_x, 130, (150, 150, 150), self.small_font, centered=True
        )

        # Stat options
        start_y = 170
        for i, (stat, name, desc) in enumerate(zip(self.stats, self.stat_names, self.stat_descriptions)):
            y = start_y + i * 80
            current_val = getattr(player, stat)

            # Highlight selected
            if i == self.selected_stat:
                # Draw selection box
                box_rect = pygame.Rect(center_x - 200, y - 10, 400, 70)
                pygame.draw.rect(screen, (60, 60, 100), box_rect)
                pygame.draw.rect(screen, (100, 150, 255), box_rect, 2)
                name_color = (255, 255, 255)
                val_color = (100, 255, 100)
            else:
                name_color = (180, 180, 180)
                val_color = (150, 200, 150)

            # Stat name and value
            self.draw_text(screen, name, center_x - 180, y + 5, name_color, self.medium_font)
            self.draw_text(screen, str(current_val), center_x + 150, y + 5, val_color, self.medium_font)

            # Description
            self.draw_text(screen, desc, center_x, y + 35, (120, 120, 150), self.small_font, centered=True)

        # Show stat effects
        y = start_y + len(self.stats) * 80 + 20
        self.draw_text(screen, "Current Bonuses:", center_x, y, (200, 200, 100), self.small_font, centered=True)
        y += 25

        # INT bonuses
        int_tier_reduction = player.intelligence // 5
        self.draw_text(
            screen,
            f"INT: -{int_tier_reduction} tier requirements",
            center_x, y, (150, 150, 200), self.small_font, centered=True
        )
        y += 20

        # WIS bonuses
        wis_ally_bonus = player.wisdom // 4
        self.draw_text(
            screen,
            f"WIS: +{wis_ally_bonus} ally defenses",
            center_x, y, (150, 150, 200), self.small_font, centered=True
        )
        y += 20

        # CHA bonuses
        cha_efficacy_mult = 1 + 0.10 * (player.charisma // 4)
        self.draw_text(
            screen,
            f"CHA: x{cha_efficacy_mult:.1f} conversion efficacy",
            center_x, y, (150, 150, 200), self.small_font, centered=True
        )
        y += 20

        # Battle bonuses (scales other stats' combat effectiveness)
        battle_scale = int((0.25 + 0.05 * player.battle) * 100)
        self.draw_text(
            screen,
            f"Battle: {battle_scale}% stat effectiveness in combat",
            center_x, y, (150, 150, 200), self.small_font, centered=True
        )


class MapView(Screen):
    """Screen where the player moves around the map."""

    def __init__(self):
        self.direction_map = {
            # Numpad
            pygame.K_KP4: (-1, 0),
            pygame.K_KP6: (1, 0),
            pygame.K_KP8: (0, -1),
            pygame.K_KP2: (0, 1),
            pygame.K_KP7: (-1, -1),
            pygame.K_KP9: (1, -1),
            pygame.K_KP1: (-1, 1),
            pygame.K_KP3: (1, 1),
            # Arrow keys
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            # Alternative numpad (uio/jkl/m,.)
            pygame.K_u: (-1, -1),
            pygame.K_i: (0, -1),
            pygame.K_o: (1, -1),
            pygame.K_j: (-1, 0),
            pygame.K_l: (1, 0),
            pygame.K_m: (-1, 1),
            pygame.K_COMMA: (0, 1),
            pygame.K_PERIOD: (1, 1),
        }
        self.font = pygame.font.SysFont("monospace", 14)
        # Auto-walk state
        self.waiting_for_walk_dir = False
        self.auto_walk_dir = None  # (dx, dy) or None
        self.last_walk_time = 0
        self.walk_delay_ms = 50  # Milliseconds between auto-walk steps

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            # Cancel auto-walk on any key
            if self.auto_walk_dir is not None:
                self.auto_walk_dir = None
                return True

            # Check for 'w' to enter walk mode
            if event.key == pygame.K_w:
                self.waiting_for_walk_dir = True
                return True

            if event.key in self.direction_map:
                dx, dy = self.direction_map[event.key]

                # If waiting for walk direction, start auto-walk
                if self.waiting_for_walk_dir:
                    self.waiting_for_walk_dir = False
                    self.auto_walk_dir = (dx, dy)
                    self.last_walk_time = pygame.time.get_ticks()
                    # Take the first step immediately
                    self._do_walk_step(game)
                    return True

                # Normal single-step movement
                self._do_move(game, dx, dy)
                return True

            # Any other key cancels waiting mode
            if self.waiting_for_walk_dir:
                self.waiting_for_walk_dir = False
                return True
        return False

    def _do_move(self, game: "game_module.Game", dx: int, dy: int) -> bool:
        """Execute a single move and handle screen transitions. Returns True if should stop auto-walk."""
        # Get player position before move
        player = None
        for p in game.gamestate.placeables or []:
            if isinstance(p, Player):
                player = p
                break
        old_x, old_y = player.x, player.y if player else (0, 0)

        game.gamestate = advance_step(game.gamestate, ("move", dx, dy))

        # Check if player hit a wall (position didn't change)
        if player and player.x == old_x and player.y == old_y:
            return True  # Stop auto-walk

        # Check status
        if game.gamestate.status == "won":
            game.current_back_screen = game.win_screen
            return True
        elif game.gamestate.status == "lost":
            game.current_back_screen = game.game_over_screen
            return True

        # Check if player used exit (pending floor advancement)
        if game.gamestate.pending_next_stage:
            game.current_back_screen = game.stat_allocation_screen
            return True

        if game.gamestate.active_encounter is not None:
            game.current_back_screen = game.encounter_start_screen
            return True

        return False  # Continue auto-walk

    def _do_walk_step(self, game: "game_module.Game") -> None:
        """Take one auto-walk step."""
        if self.auto_walk_dir is None:
            return
        dx, dy = self.auto_walk_dir
        should_stop = self._do_move(game, dx, dy)
        if should_stop:
            self.auto_walk_dir = None

    def update(self, game: "game_module.Game") -> None:
        """Called each frame for auto-walk updates."""
        if self.auto_walk_dir is None:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_walk_time >= self.walk_delay_ms:
            self.last_walk_time = current_time
            self._do_walk_step(game)

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)

        # Draw all visible placeables except player first
        for placeable in game.gamestate.placeables or []:
            if placeable.visible and not isinstance(placeable, Player):
                game.sprite_manager.draw(
                    screen,
                    placeable.x,
                    placeable.y,
                    placeable.symbol,
                    placeable.color,
                    placeable.bg_color,
                )

        # Draw player
        for placeable in game.gamestate.placeables or []:
            if isinstance(placeable, Player):
                game.sprite_manager.draw(
                    screen,
                    placeable.x,
                    placeable.y,
                    placeable.symbol,
                    placeable.color,
                    placeable.bg_color,
                )

        # Draw info in left panel
        self.draw_text(screen, f"Level: {game.gamestate.current_stage}/{game.gamestate.max_stages}", 10, 10, (255, 255, 255), self.font)

        # Show walk mode indicator in left panel
        if self.waiting_for_walk_dir:
            self.draw_text(screen, "Walk: press", 10, 30, (255, 255, 0), self.font)
            self.draw_text(screen, "direction", 10, 46, (255, 255, 0), self.font)
        elif self.auto_walk_dir is not None:
            self.draw_text(screen, "Walking...", 10, 30, (200, 200, 0), self.font)
            self.draw_text(screen, "(any key", 10, 46, (200, 200, 0), self.font)
            self.draw_text(screen, "to stop)", 10, 62, (200, 200, 0), self.font)

class EncounterStartScreen(Screen):
    """Screen shown when the player first encounters something."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 14)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                game.current_back_screen = game.encounter_screen
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)

        center_x = self.get_map_area_center_x(screen, game)

        self.draw_text(screen, "ENCOUNTER!", center_x, screen.get_height() // 3, (255, 255, 0), self.font, centered=True)
        self.draw_text(screen, "You encountered something!", center_x, screen.get_height() // 2, (200, 200, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER or SPACE to continue", center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)


class EncounterScreen(Screen):
    """Main tactical battle screen for encounters."""

    def __init__(self):
        self.mode = EncounterMode.NORMAL
        self.selected_side = "enemy"  # "player" or "enemy"
        self.selected_index = 4  # Index 0-8 in the grid (default to middle)
        self.move_source_idx = None  # Index of unit being moved
        self.font = pygame.font.SysFont("monospace", 14)
        self.small_font = pygame.font.SysFont("monospace", 12)
        self.header_font = pygame.font.SysFont("monospace", 18, bold=True)
        self.target_selection_map = {
            # Numpad keys
            pygame.K_KP7: (0, 0), pygame.K_KP8: (1, 0), pygame.K_KP9: (2, 0),
            pygame.K_KP4: (0, 1), pygame.K_KP5: (1, 1), pygame.K_KP6: (2, 1),
            pygame.K_KP1: (0, 2), pygame.K_KP2: (1, 2), pygame.K_KP3: (2, 2),
            # Number row keys
            pygame.K_7: (0, 0), pygame.K_8: (1, 0), pygame.K_9: (2, 0),
            pygame.K_4: (0, 1), pygame.K_5: (1, 1), pygame.K_6: (2, 1),
            pygame.K_1: (0, 2), pygame.K_2: (1, 2), pygame.K_3: (2, 2),
            # Alternative keyboard numpad (uio/jkl/m,.)
            pygame.K_u: (0, 0), pygame.K_i: (1, 0), pygame.K_o: (2, 0),
            pygame.K_j: (0, 1), pygame.K_k: (1, 1), pygame.K_l: (2, 1),
            pygame.K_m: (0, 2), pygame.K_COMMA: (1, 2), pygame.K_PERIOD: (2, 2),
        }

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
                if event.key in self.target_selection_map:
                    target_x, target_y = self.target_selection_map[event.key]
                    action_type = "attack" if self.mode == EncounterMode.ATTACK else "convert"
                    game.gamestate = advance_step(game.gamestate, (action_type, target_x, target_y))
                    
                    # Check win/lose conditions
                    if game.gamestate.status == "won":
                        game.current_back_screen = game.win_screen
                        return True
                    elif game.gamestate.status == "lost":
                        game.current_back_screen = game.game_over_screen
                        return True

                    self.mode = EncounterMode.NORMAL
                    if game.gamestate.active_encounter is None:
                        # Battle ended - show results screen first
                        if game.gamestate.last_battle_results:
                            game.battle_results_screen.set_results(
                                game.gamestate.last_battle_results,
                                game.gamestate.pending_recruits
                            )
                            game.current_back_screen = game.battle_results_screen
                        elif game.gamestate.pending_recruits:
                            game.current_back_screen = game.team_arrangement_screen
                        else:
                            game.current_back_screen = game.map_view
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.mode = EncounterMode.NORMAL
                    return True
            
            elif self.mode in (EncounterMode.SELECTING_ALLY, EncounterMode.SELECTING_ENEMY):
                if event.key in self.target_selection_map:
                    grid_x, grid_y = self.target_selection_map[event.key]
                    grid_index = grid_y * ENCOUNTER_GRID_WIDTH + grid_x
                    
                    if self.mode == EncounterMode.SELECTING_ALLY:
                        self.selected_side = "player"
                    else:
                        self.selected_side = "enemy"
                    self.selected_index = grid_index
                    self.mode = EncounterMode.NORMAL
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.mode = EncounterMode.NORMAL
                    return True
            
            elif self.mode == EncounterMode.SELECTING_MOVE_SOURCE:
                if event.key in self.target_selection_map:
                    grid_x, grid_y = self.target_selection_map[event.key]
                    grid_index = grid_y * ENCOUNTER_GRID_WIDTH + grid_x
                    # Check if there's a unit to move
                    team = game.gamestate.active_encounter.player_team
                    if team and team[grid_index] is not None:
                        self.move_source_idx = grid_index
                        self.mode = EncounterMode.SELECTING_MOVE_TARGET
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.mode = EncounterMode.NORMAL
                    return True

            elif self.mode == EncounterMode.SELECTING_MOVE_TARGET:
                if event.key in self.target_selection_map:
                    grid_x, grid_y = self.target_selection_map[event.key]
                    target_idx = grid_y * ENCOUNTER_GRID_WIDTH + grid_x
                    # Calculate direction
                    src_col = self.move_source_idx % 3
                    src_row = self.move_source_idx // 3
                    dx = grid_x - src_col
                    dy = grid_y - src_row
                    # Only allow orthogonal movement
                    if abs(dx) + abs(dy) == 1:
                        game.gamestate = advance_step(game.gamestate, ("move_unit", self.move_source_idx, (dx, dy)))
                    self.mode = EncounterMode.NORMAL
                    self.move_source_idx = None
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.mode = EncounterMode.NORMAL
                    self.move_source_idx = None
                    return True

            else: # Normal Mode
                if event.key == pygame.K_a:
                    self.mode = EncounterMode.ATTACK
                    return True
                elif event.key == pygame.K_c:
                    self.mode = EncounterMode.CONVERT
                    return True
                elif event.key == pygame.K_v:
                    self.mode = EncounterMode.SELECTING_MOVE_SOURCE
                    return True
                elif event.key == pygame.K_q:
                    self.mode = EncounterMode.SELECTING_ALLY
                    return True
                elif event.key == pygame.K_e:
                    self.mode = EncounterMode.SELECTING_ENEMY
                    return True
                elif event.key == pygame.K_f:
                    game.gamestate.active_encounter = None
                    game.current_back_screen = game.map_view
                    return True
                elif event.key == pygame.K_ESCAPE:
                    return False

        return False

    def _get_selected_entity(self, game: "game_module.Game") -> Optional[Union[Creature, Player]]:
        if game.gamestate.active_encounter is None:
            return None
        
        team = None
        if self.selected_side == "player":
            team = game.gamestate.active_encounter.player_team
        else:
            team = game.gamestate.active_encounter.enemy_team
            
        if team and self.selected_index < len(team):
            return team[self.selected_index]
        return None

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        if game.gamestate.active_encounter is None:
            return

        screen.fill((0, 0, 0))

        # Draw left panel
        self.draw_left_panel(screen, game)
        panel_width = self.get_panel_width_pixels(game)

        # Layout calculations - map area only (excluding left panel)
        width, height = screen.get_width(), screen.get_height()
        map_area_width = width - panel_width
        half_width = panel_width + map_area_width // 2
        half_height = height // 2

        # Draw Vertical Divider
        pygame.draw.line(screen, (100, 100, 100), (half_width, 0), (half_width, height))
        # Draw Horizontal Divider (map area only)
        pygame.draw.line(screen, (100, 100, 100), (panel_width, half_height), (width, half_height))

        # --- INFO PANEL (Left quadrant of map area) ---
        info_x = panel_width + 10
        self.draw_text(screen, "BATTLE INFO", info_x, 20, (255, 255, 0), self.header_font)

        selected_entity = self._get_selected_entity(game)
        if selected_entity:
            side_label = "Ally" if self.selected_side == "player" else "Enemy"
            name = getattr(selected_entity, "name", "Unknown")

            self.draw_text(screen, f"{side_label}: {name}", info_x, 50, (200, 200, 200), self.font)

            hp_color = (0, 255, 0) if selected_entity.current_health > 30 else (255, 100, 100)
            self.draw_text(screen, f"HP: {selected_entity.current_health}/{selected_entity.max_health}", info_x, 75, hp_color, self.font)

            # Defense stats
            y_offset = 93
            defense = getattr(selected_entity, "defense", getattr(selected_entity, "base_defense", 0))
            dodge = getattr(selected_entity, "dodge", getattr(selected_entity, "base_dodge", 0))
            resistance = getattr(selected_entity, "resistance", getattr(selected_entity, "base_resistance", 0))
            self.draw_text(screen, f"DEF:{defense} DOD:{dodge} RES:{resistance}", info_x, y_offset, (150, 200, 150), self.small_font)
            y_offset += 16

            # Conversion progress (for enemies)
            if hasattr(selected_entity, "conversion_progress"):
                progress = getattr(selected_entity, "conversion_progress", 0)
                max_conv = selected_entity.max_health
                self.draw_text(screen, f"Convert: {progress}/{max_conv}", info_x, y_offset, (150, 150, 255), self.small_font)
                y_offset += 16

            # Attacks
            attacks = getattr(selected_entity, "attacks", [])
            if attacks:
                self.draw_text(screen, "Attacks:", info_x, y_offset, (255, 200, 100), self.small_font)
                y_offset += 14
                for attack in attacks[:3]:  # Limit display
                    atk_text = f"  {attack.attack_type}: {attack.damage}"
                    if attack.range_min and attack.range_max:
                        atk_text += f" ({attack.range_min}-{attack.range_max})"
                    if attack.abilities:
                        atk_text += f" [{', '.join(attack.abilities[:2])}]"
                    self.draw_text(screen, atk_text, info_x, y_offset, (200, 180, 100), self.small_font)
                    y_offset += 14

            # Abilities
            abilities = getattr(selected_entity, "abilities", [])
            if abilities:
                self.draw_text(screen, "Abilities:", info_x, y_offset, (100, 200, 255), self.small_font)
                y_offset += 14
                for ability in abilities[:3]:  # Limit display
                    self.draw_text(screen, f"  {ability}", info_x, y_offset, (150, 200, 255), self.small_font)
                    y_offset += 14

            # Debuffs
            debuffs = getattr(selected_entity, "debuffs", {})
            if debuffs:
                self.draw_text(screen, "Debuffs:", info_x, y_offset, (255, 100, 100), self.small_font)
                y_offset += 14
                for debuff, stacks in debuffs.items():
                    self.draw_text(screen, f"  {debuff} x{stacks}", info_x, y_offset, (255, 150, 150), self.small_font)
                    y_offset += 14
        else:
            self.draw_text(screen, "No selection / Empty slot", info_x, 85, (150, 150, 150), self.font)

        # --- BATTLE GRID (Right Top) ---
        # Grid is 6 tiles wide (3 player + 3 enemy), 3 tiles high
        # Use 2x scale for larger battle grid
        grid_scale = 2
        tile_w = game.sprite_manager.tile_width * grid_scale
        tile_h = game.sprite_manager.tile_height * grid_scale
        grid_width_pixels = 6 * tile_w
        grid_height_pixels = 3 * tile_h

        # Right quadrant width (from half_width to screen edge)
        right_quadrant_width = width - half_width
        grid_start_x = half_width + (right_quadrant_width - grid_width_pixels) // 2
        grid_start_y = (half_height - grid_height_pixels) // 2

        # Draw Grid Highlights
        self._render_highlights(screen, game, grid_start_x, grid_start_y, tile_w, tile_h)

        # Draw Grid Entities
        player_team = game.gamestate.active_encounter.player_team
        enemy_team = game.gamestate.active_encounter.enemy_team

        # Draw Player Team (Offset 0)
        self._render_team(screen, game, player_team, grid_start_x, grid_start_y, 0, grid_scale)
        # Draw Enemy Team (Offset 3)
        self._render_team(screen, game, enemy_team, grid_start_x, grid_start_y, 3, grid_scale)

        # --- ACTIONS PANEL (Right Bottom) ---
        action_x = half_width + 20
        action_y = half_height + 20
        self.draw_text(screen, "ACTIONS", action_x, action_y, (255, 255, 0), self.header_font)
        
        instructions = []
        if self.mode == EncounterMode.ATTACK:
            instructions = [("Select ATTACK target:", (255, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode == EncounterMode.CONVERT:
            instructions = [("Select CONVERT target:", (150, 150, 255)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode == EncounterMode.SELECTING_MOVE_SOURCE:
            instructions = [("Select unit to MOVE:", (100, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode == EncounterMode.SELECTING_MOVE_TARGET:
            instructions = [("Select adjacent square:", (100, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode in (EncounterMode.SELECTING_ALLY, EncounterMode.SELECTING_ENEMY):
            target = "ALLY" if self.mode == EncounterMode.SELECTING_ALLY else "ENEMY"
            instructions = [(f"Inspect {target}:", (255, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        else:
            instructions = [
                ("[A] Attack", (200, 200, 200)),
                ("[C] Convert", (200, 200, 200)),
                ("[V] Move unit", (200, 200, 200)),
                ("[Q] Inspect Ally", (200, 200, 200)),
                ("[E] Inspect Enemy", (200, 200, 200)),
                ("[F] Flee", (200, 200, 200))
            ]

        for i, (text, color) in enumerate(instructions):
            self.draw_text(screen, text, action_x, action_y + 40 + i * 25, color, self.font)

        # --- COMBAT LOG (Left Bottom) ---
        log_x = panel_width + 10
        log_y = half_height + 10
        self.draw_text(screen, "COMBAT LOG", log_x, log_y, (255, 255, 0), self.header_font)

        combat_log = getattr(game.gamestate.active_encounter, "combat_log", []) or []
        # Show most recent entries that fit (scroll from bottom)
        log_line_height = 16
        max_lines = (height - half_height - 50) // log_line_height
        recent_log = combat_log[-max_lines:] if len(combat_log) > max_lines else combat_log

        log_y += 30
        for entry in recent_log:
            # Color code different log entry types
            if entry.startswith("---"):
                color = (150, 150, 150)  # Turn markers
            elif "defeated" in entry:
                color = (255, 100, 100)  # Deaths
            elif "joins" in entry:
                color = (100, 255, 100)  # Recruits
            elif "converts" in entry:
                color = (150, 150, 255)  # Conversion
            elif "evades" in entry:
                color = (255, 255, 100)  # Evasion
            elif "heals" in entry:
                color = (100, 255, 150)  # Healing
            else:
                color = (200, 200, 200)  # Default

            # Truncate long entries - combat log is in left quadrant (panel_width to half_width)
            left_quadrant_width = half_width - panel_width
            max_chars = (left_quadrant_width - 20) // 7  # Approximate char width
            display_entry = entry[:max_chars] if len(entry) > max_chars else entry
            self.draw_text(screen, display_entry, log_x, log_y, color, self.small_font)
            log_y += log_line_height

    def _calculate_position_damage(self, game: "game_module.Game", target_row: int, target_col: int, for_conversion: bool) -> int:
        """Calculate total base damage all allies can deal to a specific enemy position.

        Uses simple targeting rules:
        - Ranged: can hit squares within attack range
        - Magic: can hit squares in the mirror column (same row position)
        - Melee: can only hit if target is the first enemy in attacker's row
        """
        if game.gamestate.active_encounter is None:
            return 0

        encounter = game.gamestate.active_encounter
        player_team = encounter.player_team
        enemy_team = encounter.enemy_team
        if not player_team:
            return 0

        total_damage = 0
        processed_units = set()  # Track 2x2 units to avoid double-counting

        for idx, unit in enumerate(player_team):
            if unit is None:
                continue

            # Skip if already processed (2x2 unit)
            if id(unit) in processed_units:
                continue
            processed_units.add(id(unit))

            attacker_row = idx // 3
            attacker_col = idx % 3

            # Get attacks for this unit
            if isinstance(unit, Player):
                attacks = get_hero_attacks(unit)
            else:
                attacks = unit.attacks or []

            if not attacks:
                continue

            # Check each attack type
            for attack in attacks:
                can_hit = False

                if attack.attack_type == "ranged":
                    # Ranged can hit squares within range
                    # Distance is column-based: attacker is in player grid (0-2), target is in enemy grid (0-2)
                    # Distance = (3 - attacker_col) + target_col (crossing the gap between grids)
                    distance = (3 - attacker_col) + target_col
                    range_min = attack.range_min or 1
                    range_max = attack.range_max or 99
                    can_hit = (range_min <= distance <= range_max)

                elif attack.attack_type == "magic":
                    # Magic hits mirror column (front->front, middle->middle, back->back)
                    # Mirror column: player col 0 (back) hits enemy col 2 (back), etc.
                    mirror_col = 2 - attacker_col
                    can_hit = (target_col == mirror_col)

                elif attack.attack_type == "melee":
                    # Melee can only hit if on same row, target is first enemy,
                    # and no ally is blocking (in front of attacker)
                    if attacker_row == target_row:
                        # Check if blocked by ally in front (columns > attacker_col for player)
                        blocked = False
                        for col in range(attacker_col + 1, 3):
                            ally_idx = attacker_row * 3 + col
                            if player_team and player_team[ally_idx] is not None:
                                blocked = True
                                break

                        if not blocked:
                            # Find first enemy in this row
                            first_enemy_col = None
                            for col in range(3):
                                enemy_idx = attacker_row * 3 + col
                                if enemy_team and enemy_team[enemy_idx] is not None:
                                    first_enemy_col = col
                                    break
                            can_hit = (first_enemy_col == target_col)

                if can_hit:
                    total_damage += 1  # Count attacks, not damage

        return total_damage

    def _render_highlights(self, screen: pygame.Surface, game: "game_module.Game", start_x: int, start_y: int, tile_w: int, tile_h: int):
        # Create a transparent surface for highlights
        highlight_surf = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)

        # Intensity-based highlighting for ATTACK/CONVERT modes
        if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
            for_conversion = (self.mode == EncounterMode.CONVERT)
            base_color = (255, 200, 50) if not for_conversion else (100, 150, 255)

            # Calculate damage for all 9 enemy positions
            damages = []
            for idx in range(9):
                row, col = idx // 3, idx % 3
                dmg = self._calculate_position_damage(game, row, col, for_conversion)
                damages.append(dmg)

            max_dmg = max(damages) if damages else 1
            if max_dmg == 0:
                max_dmg = 1  # Avoid division by zero

            # Render each cell with intensity based on damage
            for idx in range(9):
                dmg = damages[idx]
                if dmg <= 0:
                    continue  # No highlight for zero damage

                # Alpha scales from 50 to 180 based on damage ratio
                alpha = int(50 + 130 * (dmg / max_dmg))
                color = (*base_color, alpha)

                row, col = idx // 3, idx % 3
                highlight_surf.fill(color)
                screen.blit(highlight_surf, (start_x + (col + 3) * tile_w, start_y + row * tile_h))

        # Uniform highlighting for other selection modes
        elif self.mode == EncounterMode.SELECTING_ALLY:
            highlight_surf.fill((100, 150, 255, 50))
            for y in range(3):
                for x in range(3):
                    screen.blit(highlight_surf, (start_x + x * tile_w, start_y + y * tile_h))

        elif self.mode == EncounterMode.SELECTING_ENEMY:
            highlight_surf.fill((150, 100, 255, 50))
            for y in range(3):
                for x in range(3, 6):
                    screen.blit(highlight_surf, (start_x + x * tile_w, start_y + y * tile_h))

    def _render_team(self, screen: pygame.Surface, game: "game_module.Game", team: list, start_x: int, start_y: int, x_offset: int, scale: int = 1):
        if not team:
            return

        tile_w = game.sprite_manager.tile_width * scale
        tile_h = game.sprite_manager.tile_height * scale

        # Track rendered 2x2 units to avoid double-rendering
        rendered_2x2 = set()

        for i, entity in enumerate(team):
            if entity is None:
                continue

            # Skip if already rendered as part of a 2x2 unit
            if id(entity) in rendered_2x2:
                continue

            grid_x = (i % 3) + x_offset
            grid_y = i // 3

            size = getattr(entity, "size", "1x1")
            if size == "2x2":
                # Mark as rendered
                rendered_2x2.add(id(entity))

                # Get the 4 glyphs or use symbol for all
                glyphs = getattr(entity, "glyphs", None) or [entity.symbol] * 4
                color = entity.color

                # Find top-left position of this 2x2 unit
                # Check all positions to find the minimum row/col
                positions = [idx for idx, e in enumerate(team) if e is entity]
                if positions:
                    min_row = min(p // 3 for p in positions)
                    min_col = min(p % 3 for p in positions)

                    # Render all 4 glyphs: TL, TR, BL, BR
                    glyph_positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
                    for (dx, dy), glyph in zip(glyph_positions, glyphs):
                        sprite = game.sprite_manager.get_sprite(glyph, color)
                        if scale > 1:
                            scaled = pygame.transform.scale(sprite, (tile_w, tile_h))
                            sprite = scaled.convert_alpha()
                        px = start_x + (min_col + dx + x_offset) * tile_w
                        py = start_y + (min_row + dy) * tile_h
                        screen.blit(sprite, (px, py))

                    # Draw damage overlay for 2x2 unit (covers all 4 tiles as one)
                    self._draw_damage_overlay(
                        screen, entity,
                        start_x + (min_col + x_offset) * tile_w,
                        start_y + min_row * tile_h,
                        tile_w * 2, tile_h * 2
                    )
            else:
                # Normal 1x1 rendering
                sprite = game.sprite_manager.get_sprite(entity.symbol, entity.color)
                if scale > 1:
                    scaled = pygame.transform.scale(sprite, (tile_w, tile_h))
                    sprite = scaled.convert_alpha()
                px = start_x + grid_x * tile_w
                py = start_y + grid_y * tile_h
                screen.blit(sprite, (px, py))

                # Draw damage overlay for 1x1 unit
                self._draw_damage_overlay(screen, entity, px, py, tile_w, tile_h)

    def _draw_damage_overlay(self, screen: pygame.Surface, entity, x: int, y: int, width: int, height: int):
        """Draw a red overlay on a unit based on damage taken.

        The overlay fills from bottom to top based on the percentage of health lost.
        A unit at 50% health has the bottom 50% covered in red.
        """
        max_health = getattr(entity, "max_health", 0)
        current_health = getattr(entity, "current_health", 0)

        if max_health <= 0:
            return

        # Calculate damage percentage (0 = full health, 1 = dead)
        damage_percent = 1.0 - (current_health / max_health)
        if damage_percent <= 0:
            return

        # Calculate overlay height (fills from bottom)
        overlay_height = int(height * damage_percent)
        if overlay_height <= 0:
            return

        # Create semi-transparent red overlay
        overlay = pygame.Surface((width, overlay_height), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 100))  # Red with ~40% opacity

        # Position at bottom of the unit
        overlay_y = y + (height - overlay_height)
        screen.blit(overlay, (x, overlay_y))
