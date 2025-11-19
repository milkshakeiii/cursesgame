# cursesgame

A simple game using python-tcod where the player moves an @ symbol around a 50x25 grid using the numpad.

The game features a screen system with multiple screens:
- **Main Menu**: Navigate menu options to start a new game or exit
- **Map View**: Play the game by moving the player around the map

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python game.py
```

## Controls

### Main Menu
- **UP/DOWN** or **Numpad 8/2**: Navigate menu options
- **ENTER**: Select menu option
- **ESC**: Quit the game

### Map View (In-Game)
- **Numpad 4**: Move left
- **Numpad 6**: Move right
- **Numpad 8**: Move up
- **Numpad 2**: Move down
- **Numpad 7**: Move up-left
- **Numpad 9**: Move up-right
- **Numpad 1**: Move down-left
- **Numpad 3**: Move down-right
- **ESC**: Quit the game

### Global Controls (All Screens)
- **Alt+Enter**: Toggle fullscreen/windowed mode

## Running Tests

```bash
python -m pytest test_game.py -v
```

## Features

- **Screen System**: Multiple screens with different functionality
  - Main Menu with selectable options (New Game, Options, Exit)
  - Map View for gameplay
- 50x25 ASCII grid
- Player represented by '@' symbol
- 8-directional movement using numpad
- Boundary checking prevents moving off the grid
- Border drawn around the play area
- Fullscreen toggle and text size adjustment
