import pygame
from typing import Dict, Optional, Tuple

BLOCK_GLYPHS = "░▒▓█"
FALLBACK_GLYPHS = {"░": ".", "▒": ":", "▓": "=", "█": "#"}
FONT_CANDIDATES = [
    "Menlo",
    "DejaVu Sans Mono",
    "Noto Sans Mono",
    "Liberation Mono",
    "Consolas",
    "Courier New",
    "Monaco",
]

class SpriteManager:
    def __init__(self, tile_size: int = 24):
        self.tile_size = tile_size
        if not pygame.font.get_init():
            pygame.font.init()
        self.font, self.block_font, self.needs_glyph_fallback = self._select_fonts()
        self.cache: Dict[
            Tuple[str, Tuple[int, int, int], Optional[Tuple[int, int, int]]],
            pygame.Surface,
        ] = {}

    def _select_fonts(self) -> Tuple[pygame.font.Font, pygame.font.Font, bool]:
        size = int(self.tile_size * 0.8)
        block_size = self.tile_size
        for name in FONT_CANDIDATES:
            font = pygame.font.SysFont(name, size)
            block_font = pygame.font.SysFont(name, block_size)
            if self._supports_glyphs(block_font, BLOCK_GLYPHS):
                return font, block_font, False
        fallback = pygame.font.SysFont("monospace", size)
        block_fallback = pygame.font.SysFont("monospace", block_size)
        return fallback, block_fallback, not self._supports_glyphs(block_fallback, BLOCK_GLYPHS)

    @staticmethod
    def _supports_glyphs(font: pygame.font.Font, text: str) -> bool:
        metrics = font.metrics(text)
        return metrics is not None and all(m is not None for m in metrics)

    def get_sprite(
        self,
        symbol: str,
        color: Tuple[int, int, int],
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> pygame.Surface:
        """
        Generates or retrieves a cached sprite surface for a given symbol and color.
        """
        render_symbol = (
            FALLBACK_GLYPHS.get(symbol, symbol) if self.needs_glyph_fallback else symbol
        )
        key = (render_symbol, color, bg_color)
        if key in self.cache:
            return self.cache[key]

        # Create a transparent surface for the tile
        surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        
        if bg_color is not None:
            surface.fill(bg_color)

        if not self.needs_glyph_fallback and render_symbol in BLOCK_GLYPHS:
            text_surf = self.block_font.render(render_symbol, False, color)
            glyph_rect = text_surf.get_bounding_rect()
            if glyph_rect.width and glyph_rect.height:
                text_surf = text_surf.subsurface(glyph_rect).copy()
            if text_surf.get_size() != (self.tile_size, self.tile_size):
                text_surf = pygame.transform.scale(
                    text_surf, (self.tile_size, self.tile_size)
                )
            surface.blit(text_surf, (0, 0))
        else:
            # Render the text
            text_surf = self.font.render(render_symbol, True, color)

            # Center the text on the tile
            text_rect = text_surf.get_rect(
                center=(self.tile_size // 2, self.tile_size // 2)
            )
            surface.blit(text_surf, text_rect)

        self.cache[key] = surface
        return surface

    def draw(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        symbol: str,
        color: Tuple[int, int, int],
        bg_color: Optional[Tuple[int, int, int]] = None,
    ):
        """
        Draws a symbol at the specified grid coordinates.
        """
        sprite = self.get_sprite(symbol, color, bg_color)
        screen_x = x * self.tile_size
        screen_y = y * self.tile_size
        screen.blit(sprite, (screen_x, screen_y))
