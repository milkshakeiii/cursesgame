#!/usr/bin/env python3
import pygame
import random
from game_data import GRID_HEIGHT, GRID_WIDTH
from gameplay import generate_map
from graphics import SpriteManager
from pygame_screens import EncounterScreen, EncounterStartScreen, MainMenu, MapView, Screen, WinScreen, GameOverScreen, BiomeOrderScreen, TeamArrangementScreen

TILE_SIZE = 24
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

class Game:
    def __init__(self, screen):
        self.gamestate = generate_map()
        self.running = True
        self.screen = screen
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.sprite_manager = SpriteManager(tile_size=TILE_SIZE)

        # Initialize screens
        self.map_view = MapView()
        self.main_menu = MainMenu()
        self.encounter_start_screen = EncounterStartScreen()
        self.encounter_screen = EncounterScreen()
        self.win_screen = WinScreen()
        self.game_over_screen = GameOverScreen()
        self.biome_order_screen = BiomeOrderScreen()
        self.team_arrangement_screen = TeamArrangementScreen()
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

    def render(self) -> None:
        self.current_screen().render(self.render_surface, self)
        # Scale render surface to fit the screen
        screen_size = self.screen.get_size()
        if screen_size == (SCREEN_WIDTH, SCREEN_HEIGHT):
            self.screen.blit(self.render_surface, (0, 0))
        else:
            scaled = pygame.transform.scale(self.render_surface, screen_size)
            self.screen.blit(scaled, (0, 0))

def main():
    pygame.init()
    pygame.display.set_caption("Simple Movement Game (Pygame)")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    game = Game(screen)
    clock = pygame.time.Clock()

    while game.running:
        for event in pygame.event.get():
            game.handle_event(event)
        
        game.render()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()