#!/usr/bin/env python3
import pygame
import pygame.freetype
import random
from game_data import GRID_HEIGHT, GRID_WIDTH
from gameplay import generate_map
from graphics import SpriteManager
from pygame_screens import EncounterScreen, EncounterStartScreen, MainMenu, MapView, Screen, WinScreen, GameOverScreen, BiomeOrderScreen, TeamArrangementScreen, BattleResultsScreen, StatAllocationScreen, ExitConfirmationScreen

SCALE = 1

# Initialize to calculate screen dimensions
pygame.freetype.init()
_temp_sm = SpriteManager(scale=SCALE)
SCREEN_WIDTH = GRID_WIDTH * _temp_sm.tile_width
SCREEN_HEIGHT = GRID_HEIGHT * _temp_sm.tile_height
del _temp_sm


class Game:
    def __init__(self, screen):
        self.gamestate = generate_map()
        self.running = True
        self.screen = screen
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.sprite_manager = SpriteManager(scale=SCALE)

        # Initialize screens
        self.map_view = MapView()
        self.main_menu = MainMenu()
        self.encounter_start_screen = EncounterStartScreen()
        self.encounter_screen = EncounterScreen()
        self.win_screen = WinScreen()
        self.game_over_screen = GameOverScreen()
        self.biome_order_screen = BiomeOrderScreen()
        self.team_arrangement_screen = TeamArrangementScreen()
        self.battle_results_screen = BattleResultsScreen()
        self.stat_allocation_screen = StatAllocationScreen()
        self.exit_confirmation_screen = ExitConfirmationScreen()
        self.current_back_screen = self.main_menu
        self.current_front_screen = None

    def reset_game(self):
        biomes = ["forest", "plains", "snow", "underground"]
        random.shuffle(biomes)
        self.gamestate = generate_map(stage=1, biome_order=biomes)

    def current_screen(self) -> Screen:
        return self.current_front_screen or self.current_back_screen

    def toggle_fullscreen(self) -> None:
        is_fullscreen = self.screen.get_flags() & pygame.FULLSCREEN
        if is_fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.current_screen().handle_event(event, self)

    def update(self) -> None:
        """Called each frame for time-based updates like auto-walk."""
        screen = self.current_screen()
        if hasattr(screen, 'update'):
            screen.update(self)

    def render(self) -> None:
        # Always render back screen first
        self.current_back_screen.render(self.render_surface, self)
        # If there's a front screen (popup), render it on top
        if self.current_front_screen:
            self.current_front_screen.render(self.render_surface, self)
        screen_size = self.screen.get_size()
        if screen_size == (SCREEN_WIDTH, SCREEN_HEIGHT):
            self.screen.blit(self.render_surface, (0, 0))
        else:
            # Scale maintaining aspect ratio with letterboxing/pillarboxing
            screen_w, screen_h = screen_size
            scale_x = screen_w / SCREEN_WIDTH
            scale_y = screen_h / SCREEN_HEIGHT
            scale = min(scale_x, scale_y)

            scaled_w = int(SCREEN_WIDTH * scale)
            scaled_h = int(SCREEN_HEIGHT * scale)
            offset_x = (screen_w - scaled_w) // 2
            offset_y = (screen_h - scaled_h) // 2

            # Fill with black for letterbox/pillarbox bars
            self.screen.fill((0, 0, 0))
            scaled = pygame.transform.scale(self.render_surface, (scaled_w, scaled_h))
            self.screen.blit(scaled, (offset_x, offset_y))

def main():
    pygame.init()
    pygame.display.set_caption("Simple Movement Game (Pygame)")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    game = Game(screen)
    clock = pygame.time.Clock()

    while game.running:
        for event in pygame.event.get():
            game.handle_event(event)

        game.update()
        game.render()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()