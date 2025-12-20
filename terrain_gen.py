"""Biome-aware terrain generation using layered simplex noise."""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import tcod.noise


@dataclass
class MazeCell:
    """Represents a cell in a maze with walls on each edge."""

    north: bool = True
    east: bool = True
    south: bool = True
    west: bool = True


def generate_maze(seed: int, n: int) -> Dict[Tuple[int, int], MazeCell]:
    """
    Generate an nxn maze using recursive backtracking.

    Args:
        seed: Random seed for reproducible generation.
        n: Size of the maze (n x n cells).

    Returns:
        Dictionary mapping (x, y) coordinates to MazeCell objects.
        Each cell tracks which of its 4 edges have walls.
    """
    rng = random.Random(seed)

    # Initialize all cells with all walls
    maze: Dict[Tuple[int, int], MazeCell] = {
        (x, y): MazeCell() for x in range(n) for y in range(n)
    }

    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
    directions = {
        "north": (0, -1),
        "east": (1, 0),
        "south": (0, 1),
        "west": (-1, 0),
    }

    def carve(x: int, y: int, visited: Set[Tuple[int, int]]) -> None:
        visited.add((x, y))

        dirs = list(directions.keys())
        rng.shuffle(dirs)

        for direction in dirs:
            dx, dy = directions[direction]
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in visited:
                # Remove wall between current and neighbor
                setattr(maze[(x, y)], direction, False)
                setattr(maze[(nx, ny)], opposite[direction], False)
                carve(nx, ny, visited)

    carve(0, 0, set())
    return maze


def maze_to_grid_walls(
    maze: Dict[Tuple[int, int], MazeCell],
    maze_size: int,
    cell_width: int,
    cell_height: int,
    grid_width: int,
    grid_height: int,
) -> Set[Tuple[int, int]]:
    """
    Convert maze cell walls to grid wall coordinates.

    Args:
        maze: Dictionary of maze cells from generate_maze().
        maze_size: The n x n size of the maze.
        cell_width: Width of each maze cell in grid tiles (interior only).
        cell_height: Height of each maze cell in grid tiles (interior only).
        grid_width: Total grid width.
        grid_height: Total grid height.

    Returns:
        Set of (x, y) coordinates where walls should be placed.
    """
    walls: Set[Tuple[int, int]] = set()

    # First, draw the complete wall grid framework (all internal wall lines)
    # Vertical wall lines at x positions between cells
    for mx in range(maze_size + 1):
        wall_x = mx * (cell_width + 1)
        # Draw full vertical line
        for y in range(maze_size * (cell_height + 1) + 1):
            walls.add((wall_x, y))

    # Horizontal wall lines at y positions between cells
    for my in range(maze_size + 1):
        wall_y = my * (cell_height + 1)
        # Draw full horizontal line
        for x in range(maze_size * (cell_width + 1) + 1):
            walls.add((x, wall_y))

    # Now carve out passages where the maze has openings
    for (mx, my), cell in maze.items():
        # Calculate grid position of this cell's top-left interior corner
        base_x = 1 + mx * (cell_width + 1)
        base_y = 1 + my * (cell_height + 1)

        # Remove north wall segment if passage exists
        if not cell.north:
            wall_y = base_y - 1
            for dx in range(cell_width):
                walls.discard((base_x + dx, wall_y))

        # Remove south wall segment if passage exists
        if not cell.south:
            wall_y = base_y + cell_height
            for dx in range(cell_width):
                walls.discard((base_x + dx, wall_y))

        # Remove west wall segment if passage exists
        if not cell.west:
            wall_x = base_x - 1
            for dy in range(cell_height):
                walls.discard((wall_x, base_y + dy))

        # Remove east wall segment if passage exists
        if not cell.east:
            wall_x = base_x + cell_width
            for dy in range(cell_height):
                walls.discard((wall_x, base_y + dy))

    # Filter to only include walls within grid bounds (excluding outer border)
    return {(x, y) for x, y in walls if 1 <= x < grid_width - 1 and 1 <= y < grid_height - 1}


def get_corner_cell_center(
    maze_size: int,
    cell_width: int,
    cell_height: int,
    corner: str,
) -> Tuple[int, int]:
    """
    Get the center grid position of a corner cell in the maze.

    Args:
        maze_size: The n x n size of the maze.
        cell_width: Width of each maze cell in grid tiles.
        cell_height: Height of each maze cell in grid tiles.
        corner: One of "TL" (top-left), "TR" (top-right), "BL" (bottom-left), "BR" (bottom-right).

    Returns:
        (x, y) grid coordinates for the center of the specified corner cell.
    """
    corners = {
        "TL": (0, 0),
        "TR": (maze_size - 1, 0),
        "BL": (0, maze_size - 1),
        "BR": (maze_size - 1, maze_size - 1),
    }
    mx, my = corners[corner]

    # Calculate cell's top-left grid position (+1 for border)
    base_x = 1 + mx * (cell_width + 1)
    base_y = 1 + my * (cell_height + 1)

    # Return center of cell
    return base_x + cell_width // 2, base_y + cell_height // 2


def _build_noise(seed: int) -> tcod.noise.Noise:
    return tcod.noise.Noise(
        dimensions=2,
        algorithm=tcod.noise.Algorithm.SIMPLEX,
        implementation=tcod.noise.Implementation.SIMPLE,
        hurst=0.5,
        lacunarity=2.0,
        octaves=2,
        seed=seed,
    )


def generate_biome_terrain(
    seed: int,
    width: int,
    height: int,
    base_tile: str,
    layers: List[Dict[str, object]],
    *,
    scale: float = 0.1,
    mirror: bool = False,
) -> Dict[Tuple[int, int], str]:
    """Generate terrain tile IDs for a biome using layered noise."""
    ordered_layers = sorted(layers, key=lambda layer: layer.get("priority", 0))
    noise_layers = [
        (layer, _build_noise(seed + int(layer.get("seed_offset", 0))))
        for layer in ordered_layers
    ]

    terrain: Dict[Tuple[int, int], str] = {}
    if mirror:
        half_height = height // 2
        y_range = range(half_height + 1)
    else:
        half_height = None
        y_range = range(height)

    for x in range(width):
        for y in y_range:
            tile_id = base_tile
            for layer, noise in noise_layers:
                threshold = float(layer["threshold"])
                if noise.get_point(x * scale, y * scale) > threshold:
                    tile_id = str(layer["tile_id"])
            terrain[(x, y)] = tile_id

            if mirror and half_height is not None and y < half_height:
                terrain[(x, height - 1 - y)] = tile_id

    return terrain
