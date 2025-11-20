#!/usr/bin/env python3
"""Unit tests for the game."""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict
from game import (Player, Game, GRID_WIDTH, GRID_HEIGHT, 
                  DEFAULT_FONT_SIZE, GameState, advance_step, Terrain, Encounter, Invisible, 
                  Visible, generate_map)
from screens import MapView, MainMenu, EncounterScreen
import tcod.event


def get_player(gamestate: GameState) -> Player:
    """Helper function to get the player from the gamestate placeables list."""
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            return placeable
    return None


class TestPlayer:
    """Tests for the Player class."""
    
    def test_player_initialization(self):
        """Test that a player initializes with correct position."""
        player = Player(10, 5)
        assert player.x == 10
        assert player.y == 5
        assert player.symbol == '@'
    
    def test_move_right(self):
        """Test moving right."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (1, 0))
        player = get_player(gamestate)
        assert player.x == 11
        assert player.y == 10
    
    def test_move_left(self):
        """Test moving left."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (-1, 0))
        player = get_player(gamestate)
        assert player.x == 9
        assert player.y == 10
    
    def test_move_up(self):
        """Test moving up."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (0, -1))
        player = get_player(gamestate)
        assert player.x == 10
        assert player.y == 9
    
    def test_move_down(self):
        """Test moving down."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (0, 1))
        player = get_player(gamestate)
        assert player.x == 10
        assert player.y == 11
    
    def test_move_upleft(self):
        """Test moving diagonally up-left."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (-1, -1))
        player = get_player(gamestate)
        assert player.x == 9
        assert player.y == 9
    
    def test_move_upright(self):
        """Test moving diagonally up-right."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (1, -1))
        player = get_player(gamestate)
        assert player.x == 11
        assert player.y == 9
    
    def test_move_downleft(self):
        """Test moving diagonally down-left."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (-1, 1))
        player = get_player(gamestate)
        assert player.x == 9
        assert player.y == 11
    
    def test_move_downright(self):
        """Test moving diagonally down-right."""
        gamestate = GameState(placeables=[Player(10, 10)])
        gamestate = advance_step(gamestate, (1, 1))
        player = get_player(gamestate)
        assert player.x == 11
        assert player.y == 11
    
    def test_move_out_of_bounds_left(self):
        """Test that moving out of bounds to the left is prevented."""
        gamestate = GameState(placeables=[Player(0, 10)])
        gamestate = advance_step(gamestate, (-1, 0))
        player = get_player(gamestate)
        assert player.x == 0
        assert player.y == 10
    
    def test_move_out_of_bounds_right(self):
        """Test that moving out of bounds to the right is prevented."""
        gamestate = GameState(placeables=[Player(GRID_WIDTH - 1, 10)])
        gamestate = advance_step(gamestate, (1, 0))
        player = get_player(gamestate)
        assert player.x == GRID_WIDTH - 1
        assert player.y == 10
    
    def test_move_out_of_bounds_up(self):
        """Test that moving out of bounds upward is prevented."""
        gamestate = GameState(placeables=[Player(10, 0)])
        gamestate = advance_step(gamestate, (0, -1))
        player = get_player(gamestate)
        assert player.x == 10
        assert player.y == 0
    
    def test_move_out_of_bounds_down(self):
        """Test that moving out of bounds downward is prevented."""
        gamestate = GameState(placeables=[Player(10, GRID_HEIGHT - 1)])
        gamestate = advance_step(gamestate, (0, 1))
        player = get_player(gamestate)
        assert player.x == 10
        assert player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_topleft_corner(self):
        """Test that moving out of bounds from top-left corner is prevented."""
        gamestate = GameState(placeables=[Player(0, 0)])
        gamestate = advance_step(gamestate, (-1, -1))
        player = get_player(gamestate)
        assert player.x == 0
        assert player.y == 0
    
    def test_move_out_of_bounds_topright_corner(self):
        """Test that moving out of bounds from top-right corner is prevented."""
        gamestate = GameState(placeables=[Player(GRID_WIDTH - 1, 0)])
        gamestate = advance_step(gamestate, (1, -1))
        player = get_player(gamestate)
        assert player.x == GRID_WIDTH - 1
        assert player.y == 0
    
    def test_move_out_of_bounds_bottomleft_corner(self):
        """Test that moving out of bounds from bottom-left corner is prevented."""
        gamestate = GameState(placeables=[Player(0, GRID_HEIGHT - 1)])
        gamestate = advance_step(gamestate, (-1, 1))
        player = get_player(gamestate)
        assert player.x == 0
        assert player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_bottomright_corner(self):
        """Test that moving out of bounds from bottom-right corner is prevented."""
        gamestate = GameState(placeables=[Player(GRID_WIDTH - 1, GRID_HEIGHT - 1)])
        gamestate = advance_step(gamestate, (1, 1))
        player = get_player(gamestate)
        assert player.x == GRID_WIDTH - 1
        assert player.y == GRID_HEIGHT - 1


class TestGame:
    """Tests for the Game class."""
    
    def test_game_initialization(self):
        """Test that a game initializes correctly."""
        game = Game()
        assert game.gamestate is not None
        player = get_player(game.gamestate)
        assert player is not None
        assert player.x == GRID_WIDTH // 2
        assert player.y == GRID_HEIGHT // 2
        assert game.running is True
    
    def test_direction_map_has_all_numpad_keys(self):
        """Test that direction map contains all 8 numpad directions."""
        game = Game()
        assert len(game.map_view.direction_map) == 8
    
    def test_game_initialization_with_context_and_font(self):
        """Test that a game initializes correctly with context and font path."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        assert game.context == mock_context
        assert game.font_path == font_path
        assert game.font_size == DEFAULT_FONT_SIZE
    
    def test_toggle_fullscreen_without_context(self):
        """Test that toggle_fullscreen does nothing without context."""
        game = Game()
        # Should not raise an exception
        game.toggle_fullscreen()
    
    def test_toggle_fullscreen_to_fullscreen(self):
        """Test toggling from windowed to fullscreen mode."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        game.toggle_fullscreen()
        
        # Should set fullscreen to True
        assert mock_window.fullscreen is True
    
    def test_toggle_fullscreen_to_windowed(self):
        """Test toggling from fullscreen to windowed mode."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = True
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        game.toggle_fullscreen()
        
        # Should set fullscreen to False
        assert mock_window.fullscreen is False
    
    def test_handle_alt_enter_event(self):
        """Test that Alt+Enter triggers fullscreen toggle."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        
        # Create Alt+Enter event
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.LALT
        )
        
        game.handle_event(event)
        
        assert mock_window.fullscreen is True


class TestMapView:
    """Tests for the MapView screen class."""
    
    def test_mapview_initialization(self):
        """Test that MapView initializes correctly."""
        map_view = MapView()
        assert len(map_view.direction_map) == 8
    
    def test_mapview_handles_quit_event(self):
        """Test that MapView handles quit events."""
        map_view = MapView()
        game = Game()
        
        event = tcod.event.Quit()
        map_view.handle_event(event, game)
        
        assert game.running is False
    
    def test_mapview_handles_escape_key(self):
        """Test that MapView handles escape key to quit."""
        map_view = MapView()
        game = Game()
        
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        
        assert game.running is False
    
    def test_mapview_handles_movement(self):
        """Test that MapView handles movement keys."""
        map_view = MapView()
        game = Game()
        player = get_player(game.gamestate)
        initial_x = player.x
        
        # Test moving right
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.KP_6,
            mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        
        player = get_player(game.gamestate)
        assert player.x == initial_x + 1
        assert player.y == player.y
    
    def test_mapview_render(self):
        """Test that MapView renders without errors."""
        map_view = MapView()
        game = Game()
        console = Mock()
        
        # Should not raise an exception
        map_view.render(console, game)
        
        # Verify console.print was called (player, borders, etc.)
        assert console.print.called


class TestMainMenu:
    """Tests for the MainMenu screen class."""
    
    def test_mainmenu_initialization(self):
        """Test that MainMenu initializes correctly."""
        menu = MainMenu()
        assert menu.options == ["New Game", "Options", "Exit"]
        assert menu.selected_index == 0
    
    def test_mainmenu_handles_quit_event(self):
        """Test that MainMenu handles quit events."""
        menu = MainMenu()
        game = Game()
        
        event = tcod.event.Quit()
        menu.handle_event(event, game)
        
        assert game.running is False
    
    def test_mainmenu_handles_escape_key(self):
        """Test that MainMenu handles escape key to quit."""
        menu = MainMenu()
        game = Game()
        
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        
        assert game.running is False
    
    def test_mainmenu_navigates_down(self):
        """Test that MainMenu navigates down through options."""
        menu = MainMenu()
        game = Game()
        
        # Initially at index 0
        assert menu.selected_index == 0
        
        # Press down
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        
        assert menu.selected_index == 1
    
    def test_mainmenu_navigates_up(self):
        """Test that MainMenu navigates up through options."""
        menu = MainMenu()
        game = Game()
        
        # Initially at index 0
        assert menu.selected_index == 0
        
        # Press up (should wrap to last option)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.UP,
            mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        
        assert menu.selected_index == 2  # Wrapped to "Exit"
    
    def test_mainmenu_selects_new_game(self):
        """Test that selecting New Game switches to MapView."""
        menu = MainMenu()
        game = Game()
        
        # Ensure we're on "New Game" (index 0)
        assert menu.selected_index == 0
        
        # Press enter to select
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        
        # Should switch to MapView
        assert game.current_back_screen == game.map_view
    
    def test_mainmenu_selects_exit(self):
        """Test that selecting Exit quits the game."""
        menu = MainMenu()
        game = Game()
        
        # Navigate to "Exit" (index 2)
        menu.selected_index = 2
        
        # Press enter to select
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_mainmenu_render(self):
        """Test that MainMenu renders without errors."""
        menu = MainMenu()
        game = Game()
        console = Mock()
        
        # Should not raise an exception
        menu.render(console, game)
        
        # Verify console.print was called
        assert console.print.called


class TestScreenIntegration:
    """Tests for screen system integration."""
    
    def test_game_starts_with_main_menu(self):
        """Test that game starts with MainMenu as current screen."""
        game = Game()
        assert isinstance(game.current_screen(), MainMenu)
    
    def test_game_has_map_view_screen(self):
        """Test that game has a MapView screen."""
        game = Game()
        assert isinstance(game.map_view, MapView)
    
    def test_game_delegates_event_to_current_screen(self):
        """Test that game delegates events to current screen."""
        game = Game()
        
        # Start with MainMenu, select New Game
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE
        )
        game.handle_event(event)
        
        # Should now be on MapView
        assert game.current_screen() == game.map_view
    
    def test_game_delegates_render_to_current_screen(self):
        """Test that game delegates rendering to current screen."""
        game = Game()
        console = Mock()
        
        # Should delegate to MainMenu (current screen)
        game.render(console)
        
        # Verify console was used
        assert console.print.called


class TestGameState:
    """Tests for the GameState class."""
    
    def test_gamestate_initialization(self):
        """Test that GameState initializes correctly."""
        player = Player(5, 10)
        gamestate = GameState(placeables=[player])
        retrieved_player = get_player(gamestate)
        assert retrieved_player == player
        assert retrieved_player.x == 5
        assert retrieved_player.y == 10
    
    def test_gamestate_is_dataclass(self):
        """Test that GameState is a dataclass."""
        player = Player(5, 10)
        gamestate = GameState(placeables=[player])
        # Dataclasses have __dataclass_fields__ attribute
        assert hasattr(gamestate, '__dataclass_fields__')


class TestSerialization:
    """Tests for serialization and deserialization of game state."""
    
    def test_gamestate_json_roundtrip(self):
        """Test that GameState with Player can be serialized to JSON and back without data loss."""
        # Create original gamestate
        original = GameState(placeables=[Player(42, 13, '&')])
        
        # Serialize to JSON string
        json_str = json.dumps(asdict(original))
        
        # Deserialize from JSON string
        parsed = json.loads(json_str)
        placeables = [Player(**p) for p in parsed['placeables']]
        deserialized = GameState(placeables=placeables)
        
        # Verify all data is preserved
        original_player = get_player(original)
        deserialized_player = get_player(deserialized)
        assert deserialized_player.x == original_player.x
        assert deserialized_player.y == original_player.y
        assert deserialized_player.symbol == original_player.symbol


class TestAdvanceStep:
    """Tests for the advance_step function."""
    
    def test_advance_step_with_no_action(self):
        """Test that advance_step returns unchanged gamestate with no action."""
        gamestate = GameState(placeables=[Player(10, 10)])
        result = advance_step(gamestate, None)
        player = get_player(result)
        assert player.x == 10
        assert player.y == 10
    
    def test_advance_step_mutates_gamestate(self):
        """Test that advance_step mutates the gamestate."""
        gamestate = GameState(placeables=[Player(10, 10)])
        result = advance_step(gamestate, (1, 0))
        # The function should mutate and return the same gamestate object
        assert result is gamestate
        player = get_player(result)
        assert player.x == 11
    
    def test_advance_step_respects_grid_bounds(self):
        """Test that advance_step respects grid bounds."""
        # Try to move out of bounds from edge
        gamestate = GameState(placeables=[Player(GRID_WIDTH - 1, GRID_HEIGHT - 1)])
        result = advance_step(gamestate, (1, 1))
        player = get_player(result)
        assert player.x == GRID_WIDTH - 1  # Should not move beyond bounds
        assert player.y == GRID_HEIGHT - 1


class TestTerrain:
    """Tests for the Terrain class."""
    
    def test_terrain_is_visible(self):
        """Test that Terrain is a Visible subclass."""
        terrain = Terrain(x=5, y=10, symbol=',', color=(50, 150, 50))
        assert isinstance(terrain, Visible)
        assert terrain.x == 5
        assert terrain.y == 10
        assert terrain.symbol == ','
        assert terrain.color == (50, 150, 50)
    
    def test_terrain_rocky(self):
        """Test rocky terrain creation."""
        terrain = Terrain(x=8, y=12, symbol='.', color=(150, 150, 150))
        assert terrain.symbol == '.'
        assert terrain.color == (150, 150, 150)


class TestEncounter:
    """Tests for the Encounter class."""
    
    def test_encounter_is_invisible(self):
        """Test that Encounter is an Invisible subclass."""
        encounter = Encounter(x=10, y=15)
        assert isinstance(encounter, Invisible)
        assert encounter.x == 10
        assert encounter.y == 15
    
    def test_encounter_not_visible(self):
        """Test that Encounter is not a Visible instance."""
        encounter = Encounter(x=10, y=15)
        assert not isinstance(encounter, Visible)


class TestGenerateMap:
    """Tests for the generate_map function."""
    
    def test_generate_map_creates_gamestate(self):
        """Test that generate_map creates a GameState."""
        gamestate = generate_map()
        assert isinstance(gamestate, GameState)
        assert gamestate.placeables is not None
        assert len(gamestate.placeables) > 0
    
    def test_generate_map_includes_player(self):
        """Test that generate_map includes a player."""
        gamestate = generate_map()
        player = get_player(gamestate)
        assert player is not None
        assert player.x == GRID_WIDTH // 2
        assert player.y == GRID_HEIGHT // 2
    
    def test_generate_map_includes_terrain(self):
        """Test that generate_map includes terrain."""
        gamestate = generate_map()
        terrain_count = sum(1 for p in gamestate.placeables if isinstance(p, Terrain))
        assert terrain_count > 0
    
    def test_generate_map_includes_encounters(self):
        """Test that generate_map includes encounters."""
        gamestate = generate_map()
        encounter_count = sum(1 for p in gamestate.placeables if isinstance(p, Encounter))
        assert encounter_count > 0


class TestEncounterDetection:
    """Tests for encounter detection in advance_step."""
    
    def test_stepping_on_encounter_sets_active_encounter(self):
        """Test that stepping on an encounter sets active_encounter."""
        player = Player(10, 10)
        encounter = Encounter(11, 10)
        gamestate = GameState(placeables=[player, encounter])
        
        # Move player onto encounter
        result = advance_step(gamestate, (1, 0))
        
        assert result.active_encounter is not None
        assert result.active_encounter == encounter
    
    def test_moving_without_encounter_leaves_active_encounter_none(self):
        """Test that moving without an encounter keeps active_encounter None."""
        player = Player(10, 10)
        gamestate = GameState(placeables=[player])
        
        # Move player
        result = advance_step(gamestate, (1, 0))
        
        assert result.active_encounter is None
    
    def test_stepping_on_non_encounter_tile_no_trigger(self):
        """Test that stepping on terrain doesn't trigger an encounter."""
        player = Player(10, 10)
        terrain = Terrain(11, 10, symbol=',', color=(50, 150, 50))
        gamestate = GameState(placeables=[player, terrain])
        
        # Move player onto terrain
        result = advance_step(gamestate, (1, 0))
        
        assert result.active_encounter is None


class TestEncounterScreen:
    """Tests for the EncounterScreen class."""
    
    def test_encounter_screen_initialization(self):
        """Test that EncounterScreen initializes correctly."""
        screen = EncounterScreen()
        assert screen is not None
    
    def test_encounter_screen_handles_quit_event(self):
        """Test that EncounterScreen handles quit events."""
        screen = EncounterScreen()
        game = Game()
        
        event = tcod.event.Quit()
        screen.handle_event(event, game)
        
        assert game.running is False
    
    def test_encounter_screen_handles_escape_key(self):
        """Test that EncounterScreen handles escape key to quit."""
        screen = EncounterScreen()
        game = Game()
        
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        
        assert game.running is False
    
    def test_encounter_screen_return_to_map_clears_encounter(self):
        """Test that returning to map clears active encounter."""
        screen = EncounterScreen()
        game = Game()
        # Set an active encounter
        encounter = Encounter(10, 10)
        game.gamestate.active_encounter = encounter
        
        # Press enter to return
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        
        # Active encounter should be cleared
        assert game.gamestate.active_encounter is None
        # Should switch back to map view
        assert game.current_back_screen == game.map_view
    
    def test_encounter_screen_space_returns_to_map(self):
        """Test that space key also returns to map."""
        screen = EncounterScreen()
        game = Game()
        game.gamestate.active_encounter = Encounter(10, 10)
        
        # Press space to return
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        
        assert game.gamestate.active_encounter is None
        assert game.current_back_screen == game.map_view
    
    def test_encounter_screen_render(self):
        """Test that EncounterScreen renders without errors."""
        screen = EncounterScreen()
        game = Game()
        console = Mock()
        
        # Should not raise an exception
        screen.render(console, game)
        
        # Verify console.print was called
        assert console.print.called


class TestMapViewEncounterIntegration:
    """Tests for MapView encounter integration."""
    
    def test_mapview_switches_to_encounter_screen_on_encounter(self):
        """Test that MapView switches to encounter screen when encounter is triggered."""
        game = Game()
        map_view = game.map_view
        
        # Set up gamestate with player and encounter
        player = Player(10, 10)
        encounter = Encounter(11, 10)
        game.gamestate = GameState(placeables=[player, encounter])
        
        # Move player onto encounter
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.KP_6,  # Move right
            mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        
        # Should have switched to encounter screen
        assert game.current_back_screen == game.encounter_screen
        assert game.gamestate.active_encounter is not None


class TestScreenBaseEventHandling:
    """Tests for base Screen class event handling (Alt+Enter and Escape)."""
    
    def test_screen_base_handles_alt_enter_on_mapview(self):
        """Test that base Screen handles Alt+Enter for fullscreen toggle on MapView."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        map_view = game.map_view
        
        # Create Alt+Enter event
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.LALT
        )
        
        map_view.handle_event(event, game)
        
        # Should toggle fullscreen
        assert mock_window.fullscreen is True
    
    def test_screen_base_handles_escape_on_mapview(self):
        """Test that base Screen handles Escape to quit on MapView."""
        game = Game()
        map_view = game.map_view
        
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE
        )
        
        map_view.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_screen_base_handles_alt_enter_on_encounter_screen(self):
        """Test that base Screen handles Alt+Enter for fullscreen toggle on EncounterScreen."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        encounter_screen = game.encounter_screen
        
        # Create Alt+Enter event
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.RALT
        )
        
        encounter_screen.handle_event(event, game)
        
        # Should toggle fullscreen
        assert mock_window.fullscreen is True
    
    def test_screen_base_handles_escape_on_encounter_screen(self):
        """Test that base Screen handles Escape to quit on EncounterScreen."""
        game = Game()
        encounter_screen = game.encounter_screen
        
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE
        )
        
        encounter_screen.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_screen_base_handles_quit_event_on_mapview(self):
        """Test that base Screen handles Quit event on MapView."""
        game = Game()
        map_view = game.map_view
        
        event = tcod.event.Quit()
        map_view.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_screen_base_handles_quit_event_on_encounter_screen(self):
        """Test that base Screen handles Quit event on EncounterScreen."""
        game = Game()
        encounter_screen = game.encounter_screen
        
        event = tcod.event.Quit()
        encounter_screen.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_screen_base_handles_quit_event_on_main_menu(self):
        """Test that base Screen handles Quit event on MainMenu."""
        game = Game()
        main_menu = game.main_menu
        
        event = tcod.event.Quit()
        main_menu.handle_event(event, game)
        
        # Should quit the game
        assert game.running is False
    
    def test_mapview_specific_event_handling_still_works(self):
        """Test that MapView's handle_specific_event still handles movement."""
        game = Game()
        map_view = game.map_view
        player = get_player(game.gamestate)
        initial_x = player.x
        
        # Test moving right (should be handled by handle_specific_event)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.KP_6,
            mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        
        player = get_player(game.gamestate)
        assert player.x == initial_x + 1
    
    def test_encounter_screen_specific_event_handling_still_works(self):
        """Test that EncounterScreen's handle_specific_event still handles return."""
        game = Game()
        encounter_screen = game.encounter_screen
        game.gamestate.active_encounter = Encounter(10, 10)
        
        # Press enter to return (should be handled by handle_specific_event)
        # Note: This is RETURN without Alt modifier, so it goes to handle_specific_event
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE
        )
        encounter_screen.handle_event(event, game)
        
        # Active encounter should be cleared
        assert game.gamestate.active_encounter is None
        assert game.current_back_screen == game.map_view
    
    def test_main_menu_specific_event_handling_still_works(self):
        """Test that MainMenu's handle_specific_event still handles navigation."""
        game = Game()
        main_menu = game.main_menu
        
        # Initially at index 0
        assert main_menu.selected_index == 0
        
        # Press down (should be handled by handle_specific_event)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE
        )
        main_menu.handle_event(event, game)
        
        # Should move to index 1
        assert main_menu.selected_index == 1


