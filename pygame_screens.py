import pygame
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Union
from enum import Enum

from game_data import GRID_HEIGHT, GRID_WIDTH, Player, Creature
from gameplay import advance_step

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
    SELECTING_ALLY = "selecting_ally"
    SELECTING_ENEMY = "selecting_enemy"

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
                     game.running = False
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

class BiomeOrderScreen(Screen):
    """Screen shown before a new run to display biome order."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 30, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                game.current_back_screen = game.map_view
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))
        self.draw_text(screen, "UPCOMING JOURNEY", screen.get_width() // 2, 50, (255, 255, 0), self.font, centered=True)
        
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
                
                self.draw_text(screen, f"{levels}: {biome_name}", screen.get_width() // 2, y_pos, color, self.small_font, centered=True)

        self.draw_text(screen, "Press ENTER to begin", screen.get_width() // 2, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)

class TeamArrangementScreen(Screen):
    """Screen for rearranging the player's team."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 20)
        self.header_font = pygame.font.SysFont("monospace", 24, bold=True)
        self.selected_area = "grid" # "grid" or "pending"
        self.selected_index = 4 # Default to center
        self.swap_source = None # (area, index)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            # --- SELECTION & MOVEMENT ---
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_KP4, pygame.K_KP6, pygame.K_KP8, pygame.K_KP2, pygame.K_KP7, pygame.K_KP9, pygame.K_KP1, pygame.K_KP3):
                if self.selected_area == "grid":
                    col = self.selected_index % 3
                    row = self.selected_index // 3
                    
                    if event.key in (pygame.K_LEFT, pygame.K_KP4): col = (col - 1) % 3
                    elif event.key in (pygame.K_RIGHT, pygame.K_KP6): col = (col + 1) % 3
                    elif event.key in (pygame.K_UP, pygame.K_KP8): row = (row - 1) % 3
                    elif event.key in (pygame.K_DOWN, pygame.K_KP2):
                        row = (row + 1) % 3
                        if row == 0 and self.selected_index // 3 == 2 and game.gamestate.pending_recruits:
                            self.selected_area = "pending"
                            self.selected_index = 0
                            return True
                    
                    # Diagonals
                    elif event.key == pygame.K_KP7: # Up-Left
                        col = (col - 1) % 3
                        row = (row - 1) % 3
                    elif event.key == pygame.K_KP9: # Up-Right
                        col = (col + 1) % 3
                        row = (row - 1) % 3
                    elif event.key == pygame.K_KP1: # Down-Left
                        col = (col - 1) % 3
                        row = (row + 1) % 3
                        if row == 0 and self.selected_index // 3 == 2 and game.gamestate.pending_recruits:
                            self.selected_area = "pending"
                            self.selected_index = 0
                            return True
                    elif event.key == pygame.K_KP3: # Down-Right
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

                    if event.key in (pygame.K_LEFT, pygame.K_KP4): 
                        self.selected_index = (self.selected_index - 1) % count
                    elif event.key in (pygame.K_RIGHT, pygame.K_KP6): 
                        self.selected_index = (self.selected_index + 1) % count
                    elif event.key in (pygame.K_UP, pygame.K_KP8, pygame.K_KP7, pygame.K_KP9):
                        self.selected_area = "grid"
                        self.selected_index = 7
                return True

            # --- ACTIONS ---
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
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
                        player.creatures[idx1], player.creatures[idx2] = player.creatures[idx2], player.creatures[idx1]
                    
                    # 2. Pending -> Grid
                    elif area1 == "pending" and area2 == "grid":
                        recruit = pending[idx1]
                        existing = player.creatures[idx2]
                        
                        if isinstance(existing, Player):
                            self.swap_source = None
                            return True

                        player.creatures[idx2] = recruit
                        if existing:
                            pending[idx1] = existing
                        else:
                            pending.pop(idx1)
                            if self.selected_area == "pending" and self.selected_index >= len(pending):
                                self.selected_index = max(0, len(pending) - 1)
                    
                    # 3. Grid -> Pending
                    elif area1 == "grid" and area2 == "pending":
                        existing = player.creatures[idx1]
                        if isinstance(existing, Player):
                            self.swap_source = None # Prevent Player -> Pending
                            return True

                        if existing:
                            recruit = pending[idx2]
                            player.creatures[idx1] = recruit
                            pending[idx2] = existing
                        else:
                            # Grid is empty, just place the recruit
                            recruit = pending[idx2]
                            player.creatures[idx1] = recruit
                            pending.pop(idx2)
                            # Move selection to the grid slot where the recruit was placed
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
                    creature = player.creatures[self.selected_index]
                    
                    if isinstance(creature, Player):
                        return True
                        
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
        
        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2
        
        self.draw_text(screen, "TEAM ARRANGEMENT", center_x, 30, (255, 255, 0), self.header_font, centered=True)
        self.draw_text(screen, "Arrows/Numpad: Move | Enter: Swap/Place | Del: Dismiss | ESC: Done", center_x, screen.get_height() - 30, (150, 150, 150), self.font, centered=True)

        player = self._get_player(game)
        if not player: return

        # --- GRID RENDER ---
        tile_size = game.sprite_manager.tile_size * 2
        grid_start_x = center_x - (1.5 * tile_size)
        grid_start_y = center_y - (2.0 * tile_size)

        for i in range(9):
            grid_x = i % 3
            grid_y = i // 3
            x = grid_start_x + grid_x * tile_size
            y = grid_start_y + grid_y * tile_size
            
            pygame.draw.rect(screen, (50, 50, 50), (x, y, tile_size, tile_size), 1)
            
            creature = player.creatures[i]
            
            if self.selected_area == "grid" and i == self.selected_index:
                pygame.draw.rect(screen, (255, 255, 0), (x, y, tile_size, tile_size), 2)
            
            if self.swap_source == ("grid", i):
                pygame.draw.rect(screen, (0, 255, 0), (x+4, y+4, tile_size-8, tile_size-8), 2)

            if creature:
                sprite = game.sprite_manager.get_sprite(creature.symbol, creature.color)
                scaled = pygame.transform.scale(sprite, (tile_size, tile_size))
                screen.blit(scaled, (x, y))
                
                if self.selected_area == "grid" and i == self.selected_index:
                     self.draw_text(screen, f"{creature.name} (Lvl {creature.level})", center_x, grid_start_y + 3 * tile_size + 20, (255, 255, 255), self.font, centered=True)

        # --- PENDING RENDER ---
        pending = game.gamestate.pending_recruits or []
        if pending:
            self.draw_text(screen, "PENDING RECRUITS", center_x, grid_start_y + 3 * tile_size + 50, (100, 200, 255), self.font, centered=True)
            
            pending_start_x = center_x - (len(pending) * tile_size) // 2
            pending_y = grid_start_y + 3 * tile_size + 80
            
            for i, creature in enumerate(pending):
                x = pending_start_x + i * tile_size
                y = pending_y
                
                pygame.draw.rect(screen, (50, 50, 50), (x, y, tile_size, tile_size), 1)
                
                # Highlight
                if self.selected_area == "pending" and i == self.selected_index:
                    pygame.draw.rect(screen, (255, 255, 0), (x, y, tile_size, tile_size), 2)
                
                if self.swap_source == ("pending", i):
                    pygame.draw.rect(screen, (0, 255, 0), (x+4, y+4, tile_size-8, tile_size-8), 2)
                
                sprite = game.sprite_manager.get_sprite(creature.symbol, creature.color)
                scaled = pygame.transform.scale(sprite, (tile_size, tile_size))
                screen.blit(scaled, (x, y))

                if self.selected_area == "pending" and i == self.selected_index:
                     self.draw_text(screen, f"{creature.name} (Lvl {creature.level})", center_x, pending_y + tile_size + 20, (200, 200, 255), self.font, centered=True)

class MainMenu(Screen):
    """Main menu screen."""

    def __init__(self):
        self.options = ["New Game", "Options", "Exit"]
        self.selected_index = 0
        self.font = pygame.font.SysFont("monospace", 30, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_KP8):
                self.selected_index = (self.selected_index - 1) % len(self.options)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_KP2):
                self.selected_index = (self.selected_index + 1) % len(self.options)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
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
        
        # Draw Title
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
        self.font = pygame.font.SysFont("monospace", 40, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                game.current_back_screen = game.main_menu
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))
        self.draw_text(screen, "VICTORY!", screen.get_width() // 2, screen.get_height() // 3, (0, 255, 0), self.font, centered=True)
        self.draw_text(screen, "You have defeated the Dragon King!", screen.get_width() // 2, screen.get_height() // 2, (200, 255, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER to return to menu", screen.get_width() // 2, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)

class GameOverScreen(Screen):
    """Screen shown when the player loses."""
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 40, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                game.current_back_screen = game.main_menu
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))
        self.draw_text(screen, "GAME OVER", screen.get_width() // 2, screen.get_height() // 3, (255, 0, 0), self.font, centered=True)
        self.draw_text(screen, "Your journey ends here.", screen.get_width() // 2, screen.get_height() // 2, (255, 200, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER to return to menu", screen.get_width() // 2, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)

class MapView(Screen):
    """Screen where the player moves around the map."""

    def __init__(self):
        self.direction_map = {
            pygame.K_KP4: (-1, 0),
            pygame.K_KP6: (1, 0),
            pygame.K_KP8: (0, -1),
            pygame.K_KP2: (0, 1),
            pygame.K_KP7: (-1, -1),
            pygame.K_KP9: (1, -1),
            pygame.K_KP1: (-1, 1),
            pygame.K_KP3: (1, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1)
        }
        self.font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in self.direction_map:
                dx, dy = self.direction_map[event.key]
                game.gamestate = advance_step(game.gamestate, ("move", dx, dy))
                
                # Check status
                if game.gamestate.status == "won":
                    game.current_back_screen = game.win_screen
                    return True
                elif game.gamestate.status == "lost":
                    game.current_back_screen = game.game_over_screen
                    return True

                if game.gamestate.active_encounter is not None:
                    game.current_back_screen = game.encounter_start_screen
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        # We assume screen size is setup to handle GRID_WIDTH * tile_size
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
        
        # Draw HUD
        self.draw_text(screen, f"Level: {game.gamestate.current_stage}/{game.gamestate.max_stages}", 10, 10, (255, 255, 255), self.font)

class EncounterStartScreen(Screen):
    """Screen shown when the player first encounters something."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 30, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20)

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                game.current_back_screen = game.encounter_screen
                return True
        return False

    def render(self, screen: pygame.Surface, game: "game_module.Game") -> None:
        screen.fill((0, 0, 0))

        center_x = screen.get_width() // 2
        
        self.draw_text(screen, "ENCOUNTER!", center_x, screen.get_height() // 3, (255, 255, 0), self.font, centered=True)
        self.draw_text(screen, "You encountered something!", center_x, screen.get_height() // 2, (200, 200, 200), self.small_font, centered=True)
        self.draw_text(screen, "Press ENTER or SPACE to continue", center_x, screen.get_height() - 60, (150, 150, 150), self.small_font, centered=True)

class EncounterScreen(Screen):
    """Main tactical battle screen for encounters."""

    def __init__(self):
        self.mode = EncounterMode.NORMAL
        self.selected_side = "enemy"  # "player" or "enemy"
        self.selected_index = 4  # Index 0-8 in the grid (default to middle)
        self.font = pygame.font.SysFont("monospace", 20)
        self.header_font = pygame.font.SysFont("monospace", 24, bold=True)
        self.target_selection_map = {
            pygame.K_KP7: (0, 0), pygame.K_7: (0, 0),
            pygame.K_KP8: (1, 0), pygame.K_8: (1, 0),
            pygame.K_KP9: (2, 0), pygame.K_9: (2, 0),
            pygame.K_KP4: (0, 1), pygame.K_4: (0, 1),
            pygame.K_KP5: (1, 1), pygame.K_5: (1, 1),
            pygame.K_KP6: (2, 1), pygame.K_6: (2, 1),
            pygame.K_KP1: (0, 2), pygame.K_1: (0, 2),
            pygame.K_KP2: (1, 2), pygame.K_2: (1, 2),
            pygame.K_KP3: (2, 2), pygame.K_3: (2, 2),
        }

    def handle_specific_event(self, event: pygame.event.Event, game: "game_module.Game") -> bool:
        if event.type == pygame.KEYDOWN:
            if self.mode in (EncounterMode.ATTACK, EncounterMode.CONVERT):
                if event.key in self.target_selection_map:
                    target_x, target_y = self.target_selection_map[event.key]
                    action_type = "attack" if self.mode == EncounterMode.ATTACK else "convert"
                    game.gamestate = advance_step(game.gamestate, (action_type, target_x, target_y))
                    
                    # Check win condition (if encounter ended by winning boss fight)
                    if game.gamestate.status == "won":
                        game.current_back_screen = game.win_screen
                        return True

                    self.mode = EncounterMode.NORMAL
                    if game.gamestate.active_encounter is None:
                        game.current_back_screen = game.team_arrangement_screen # Switch to arrangement screen
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
            
            else: # Normal Mode
                if event.key == pygame.K_a:
                    self.mode = EncounterMode.ATTACK
                    return True
                elif event.key == pygame.K_c:
                    self.mode = EncounterMode.CONVERT
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

        # Layout calculations
        width, height = screen.get_width(), screen.get_height()
        half_width = width // 2
        half_height = height // 2

        # Draw Vertical Divider
        pygame.draw.line(screen, (100, 100, 100), (half_width, 0), (half_width, height))
        # Draw Horizontal Divider (Right Side)
        pygame.draw.line(screen, (100, 100, 100), (half_width, half_height), (width, half_height))

        # --- INFO PANEL (Left) ---
        self.draw_text(screen, "BATTLE INFO", 20, 20, (255, 255, 0), self.header_font)
        
        selected_entity = self._get_selected_entity(game)
        if selected_entity:
            side_label = "Ally" if self.selected_side == "player" else "Enemy"
            name = getattr(selected_entity, "name", "Unknown")
            
            self.draw_text(screen, f"{side_label}: {name}", 20, 60, (200, 200, 200), self.font)
            
            hp_color = (0, 255, 0) if selected_entity.current_health > 30 else (255, 100, 100)
            self.draw_text(screen, f"HP: {selected_entity.current_health}/{selected_entity.max_health}", 20, 90, hp_color, self.font)
            
            if hasattr(selected_entity, "current_convert"):
                self.draw_text(screen, f"Convert: {selected_entity.current_convert}/100", 20, 120, (150, 150, 255), self.font)
        else:
            self.draw_text(screen, "No selection / Empty slot", 20, 60, (150, 150, 150), self.font)

        # --- BATTLE GRID (Right Top) ---
        # Grid is 6 tiles wide (3 player + 3 enemy), 3 tiles high
        tile_size = game.sprite_manager.tile_size
        grid_width_pixels = 6 * tile_size
        grid_height_pixels = 3 * tile_size
        
        grid_start_x = half_width + (half_width - grid_width_pixels) // 2
        grid_start_y = (half_height - grid_height_pixels) // 2

        # Draw Grid Highlights
        self._render_highlights(screen, game, grid_start_x, grid_start_y, tile_size)

        # Draw Grid Entities
        player_team = game.gamestate.active_encounter.player_team
        enemy_team = game.gamestate.active_encounter.enemy_team
        
        # Draw Player Team (Offset 0)
        self._render_team(screen, game, player_team, grid_start_x, grid_start_y, 0)
        # Draw Enemy Team (Offset 3)
        self._render_team(screen, game, enemy_team, grid_start_x, grid_start_y, 3)

        # --- ACTIONS PANEL (Right Bottom) ---
        action_x = half_width + 20
        action_y = half_height + 20
        self.draw_text(screen, "ACTIONS", action_x, action_y, (255, 255, 0), self.header_font)
        
        instructions = []
        if self.mode == EncounterMode.ATTACK:
            instructions = [("Select ATTACK target:", (255, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode == EncounterMode.CONVERT:
            instructions = [("Select CONVERT target:", (150, 150, 255)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        elif self.mode in (EncounterMode.SELECTING_ALLY, EncounterMode.SELECTING_ENEMY):
            target = "ALLY" if self.mode == EncounterMode.SELECTING_ALLY else "ENEMY"
            instructions = [(f"Select {target}:", (255, 255, 100)), ("Use numpad 1-9", (200, 200, 200)), ("ESC to cancel", (150, 150, 150))]
        else:
            instructions = [
                ("[A] Attack", (200, 200, 200)),
                ("[C] Convert", (200, 200, 200)),
                ("[Q] Select Ally", (200, 200, 200)),
                ("[E] Select Enemy", (200, 200, 200)),
                ("[F] Flee", (200, 200, 200))
            ]

        for i, (text, color) in enumerate(instructions):
            self.draw_text(screen, text, action_x, action_y + 40 + i * 25, color, self.font)

    def _render_highlights(self, screen: pygame.Surface, game: "game_module.Game", start_x: int, start_y: int, tile_size: int):
        # Create a transparent surface for highlights
        highlight_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        
        # Determine active region to highlight
        active_region = None # (start_col, end_col, color)
        
        if self.mode == EncounterMode.ATTACK:
            active_region = (3, 6, (255, 255, 100, 50)) # Enemy side, Yellow tint
        elif self.mode == EncounterMode.CONVERT:
            active_region = (3, 6, (150, 150, 255, 50)) # Enemy side, Blue tint
        elif self.mode == EncounterMode.SELECTING_ALLY:
            active_region = (0, 3, (100, 150, 255, 50)) # Player side
        elif self.mode == EncounterMode.SELECTING_ENEMY:
            active_region = (3, 6, (150, 100, 255, 50)) # Enemy side

        if active_region:
            col_start, col_end, color = active_region
            highlight_surf.fill(color)
            for y in range(3):
                for x in range(col_start, col_end):
                    screen.blit(highlight_surf, (start_x + x * tile_size, start_y + y * tile_size))
        
        # Highlight Selected Entity (Cursor)
        cursor_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        cursor_surf.fill((255, 255, 255, 50)) # White highlight
        pygame.draw.rect(cursor_surf, (255, 255, 255), cursor_surf.get_rect(), 2) # Border

        sel_x_offset = 0 if self.selected_side == "player" else 3
        sel_x = (self.selected_index % 3) + sel_x_offset
        sel_y = self.selected_index // 3
        
        screen.blit(cursor_surf, (start_x + sel_x * tile_size, start_y + sel_y * tile_size))

    def _render_team(self, screen: pygame.Surface, game: "game_module.Game", team: list, start_x: int, start_y: int, x_offset: int):
        if not team: return
        for i, entity in enumerate(team):
            if entity:
                grid_x = (i % 3) + x_offset
                grid_y = i // 3
                sprite = game.sprite_manager.get_sprite(entity.symbol, entity.color)
                screen.blit(sprite, (start_x + grid_x * game.sprite_manager.tile_size, start_y + grid_y * game.sprite_manager.tile_size))
