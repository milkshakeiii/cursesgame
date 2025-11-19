#!/usr/bin/env python3
"""Unit tests for the game."""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict
from game import Player, Game, MapView, MainMenu, GRID_WIDTH, GRID_HEIGHT, DEFAULT_FONT_SIZE, GameState, advance_step
import tcod.event


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
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (1, 0))
        assert gamestate.player.x == 11
        assert gamestate.player.y == 10
    
    def test_move_left(self):
        """Test moving left."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (-1, 0))
        assert gamestate.player.x == 9
        assert gamestate.player.y == 10
    
    def test_move_up(self):
        """Test moving up."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (0, -1))
        assert gamestate.player.x == 10
        assert gamestate.player.y == 9
    
    def test_move_down(self):
        """Test moving down."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (0, 1))
        assert gamestate.player.x == 10
        assert gamestate.player.y == 11
    
    def test_move_upleft(self):
        """Test moving diagonally up-left."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (-1, -1))
        assert gamestate.player.x == 9
        assert gamestate.player.y == 9
    
    def test_move_upright(self):
        """Test moving diagonally up-right."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (1, -1))
        assert gamestate.player.x == 11
        assert gamestate.player.y == 9
    
    def test_move_downleft(self):
        """Test moving diagonally down-left."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (-1, 1))
        assert gamestate.player.x == 9
        assert gamestate.player.y == 11
    
    def test_move_downright(self):
        """Test moving diagonally down-right."""
        gamestate = GameState(player=Player(10, 10))
        gamestate = advance_step(gamestate, (1, 1))
        assert gamestate.player.x == 11
        assert gamestate.player.y == 11
    
    def test_move_out_of_bounds_left(self):
        """Test that moving out of bounds to the left is prevented."""
        gamestate = GameState(player=Player(0, 10))
        gamestate = advance_step(gamestate, (-1, 0))
        assert gamestate.player.x == 0
        assert gamestate.player.y == 10
    
    def test_move_out_of_bounds_right(self):
        """Test that moving out of bounds to the right is prevented."""
        gamestate = GameState(player=Player(GRID_WIDTH - 1, 10))
        gamestate = advance_step(gamestate, (1, 0))
        assert gamestate.player.x == GRID_WIDTH - 1
        assert gamestate.player.y == 10
    
    def test_move_out_of_bounds_up(self):
        """Test that moving out of bounds upward is prevented."""
        gamestate = GameState(player=Player(10, 0))
        gamestate = advance_step(gamestate, (0, -1))
        assert gamestate.player.x == 10
        assert gamestate.player.y == 0
    
    def test_move_out_of_bounds_down(self):
        """Test that moving out of bounds downward is prevented."""
        gamestate = GameState(player=Player(10, GRID_HEIGHT - 1))
        gamestate = advance_step(gamestate, (0, 1))
        assert gamestate.player.x == 10
        assert gamestate.player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_topleft_corner(self):
        """Test that moving out of bounds from top-left corner is prevented."""
        gamestate = GameState(player=Player(0, 0))
        gamestate = advance_step(gamestate, (-1, -1))
        assert gamestate.player.x == 0
        assert gamestate.player.y == 0
    
    def test_move_out_of_bounds_topright_corner(self):
        """Test that moving out of bounds from top-right corner is prevented."""
        gamestate = GameState(player=Player(GRID_WIDTH - 1, 0))
        gamestate = advance_step(gamestate, (1, -1))
        assert gamestate.player.x == GRID_WIDTH - 1
        assert gamestate.player.y == 0
    
    def test_move_out_of_bounds_bottomleft_corner(self):
        """Test that moving out of bounds from bottom-left corner is prevented."""
        gamestate = GameState(player=Player(0, GRID_HEIGHT - 1))
        gamestate = advance_step(gamestate, (-1, 1))
        assert gamestate.player.x == 0
        assert gamestate.player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_bottomright_corner(self):
        """Test that moving out of bounds from bottom-right corner is prevented."""
        gamestate = GameState(player=Player(GRID_WIDTH - 1, GRID_HEIGHT - 1))
        gamestate = advance_step(gamestate, (1, 1))
        assert gamestate.player.x == GRID_WIDTH - 1
        assert gamestate.player.y == GRID_HEIGHT - 1


class TestGame:
    """Tests for the Game class."""
    
    def test_game_initialization(self):
        """Test that a game initializes correctly."""
        game = Game()
        assert game.gamestate is not None
        assert game.gamestate.player is not None
        assert game.gamestate.player.x == GRID_WIDTH // 2
        assert game.gamestate.player.y == GRID_HEIGHT // 2
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
        initial_x = game.gamestate.player.x
        
        # Test moving right
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.KP_6,
            mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        
        assert game.gamestate.player.x == initial_x + 1
        assert game.gamestate.player.y == game.gamestate.player.y
    
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
        assert game.current_screen == game.map_view
    
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
        assert isinstance(game.current_screen, MainMenu)
    
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
        assert game.current_screen == game.map_view
    
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
        gamestate = GameState(player=player)
        assert gamestate.player == player
        assert gamestate.player.x == 5
        assert gamestate.player.y == 10
    
    def test_gamestate_is_dataclass(self):
        """Test that GameState is a dataclass."""
        player = Player(5, 10)
        gamestate = GameState(player=player)
        # Dataclasses have __dataclass_fields__ attribute
        assert hasattr(gamestate, '__dataclass_fields__')


class TestSerialization:
    """Tests for serialization and deserialization of game state."""
    
    def test_gamestate_json_roundtrip(self):
        """Test that GameState with Player can be serialized to JSON and back without data loss."""
        # Create original gamestate
        original = GameState(player=Player(42, 13, '&'))
        
        # Serialize to JSON string
        json_str = json.dumps(asdict(original))
        
        # Deserialize from JSON string
        parsed = json.loads(json_str)
        player = Player(**parsed['player'])
        deserialized = GameState(player=player)
        
        # Verify all data is preserved
        assert deserialized.player.x == original.player.x
        assert deserialized.player.y == original.player.y
        assert deserialized.player.symbol == original.player.symbol


class TestAdvanceStep:
    """Tests for the advance_step function."""
    
    def test_advance_step_with_no_action(self):
        """Test that advance_step returns unchanged gamestate with no action."""
        gamestate = GameState(player=Player(10, 10))
        result = advance_step(gamestate, None)
        assert result.player.x == 10
        assert result.player.y == 10
    
    def test_advance_step_mutates_gamestate(self):
        """Test that advance_step mutates the gamestate."""
        gamestate = GameState(player=Player(10, 10))
        result = advance_step(gamestate, (1, 0))
        # The function should mutate and return the same gamestate object
        assert result is gamestate
        assert result.player.x == 11
    
    def test_advance_step_respects_grid_bounds(self):
        """Test that advance_step respects grid bounds."""
        # Try to move out of bounds from edge
        gamestate = GameState(player=Player(GRID_WIDTH - 1, GRID_HEIGHT - 1))
        result = advance_step(gamestate, (1, 1))
        assert result.player.x == GRID_WIDTH - 1  # Should not move beyond bounds
        assert result.player.y == GRID_HEIGHT - 1


