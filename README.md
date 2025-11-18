# cursesgame

A simple game using python-tcod where the player moves an @ symbol around an 80x25 grid using the numpad.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python game.py
```

## Controls

- **Numpad 4**: Move left
- **Numpad 6**: Move right
- **Numpad 8**: Move up
- **Numpad 2**: Move down
- **Numpad 7**: Move up-left
- **Numpad 9**: Move up-right
- **Numpad 1**: Move down-left
- **Numpad 3**: Move down-right
- **ESC**: Quit the game

## Running Tests

```bash
python -m pytest test_game.py -v
```

## Features

- 80x25 ASCII grid
- Player represented by '@' symbol
- 8-directional movement using numpad
- Boundary checking prevents moving off the grid
- Border drawn around the play area