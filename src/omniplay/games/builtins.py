from omniplay.configs.game_params import NoGameParams
from omniplay.games.breakthrough.breakthrough import BreakthroughEngine
from omniplay.games.connect_four.connect_four import ConnectFourEngine
from omniplay.games.nim.inverse_nim import InverseNimEngine
from omniplay.games.nim.modified_nim import ModifiedNimEngine
from omniplay.games.nim.nim import NimEngine, NimGameParams
from omniplay.games.nim.story_nim import StoryNimEngine
from omniplay.games.spec import GameSpec
from omniplay.games.tic_tac_toe.magic_square import MagicSquareEngine, MagicSquareGameParams
from omniplay.games.tic_tac_toe.modified_tic_tac_toe import ModifiedTicTacToeEngine
from omniplay.games.tic_tac_toe.story_magic_square import StoryMagicSquareEngine
from omniplay.games.tic_tac_toe.tic_tac_toe import TicTacToeEngine
from omniplay.registry import Registry

# Built-in game specs. External games register their own GameSpec into op.registry the same way.
_BUILTIN_GAMES: list[GameSpec] = [
    # tic tac toe games
    GameSpec("tic_tac_toe", NoGameParams, TicTacToeEngine, solvable=True),
    GameSpec("modified_tic_tac_toe", NoGameParams, ModifiedTicTacToeEngine, solvable=True),
    GameSpec("magic_square", MagicSquareGameParams, MagicSquareEngine, solvable=True),
    GameSpec("story_magic_square", MagicSquareGameParams, StoryMagicSquareEngine, solvable=True),
    # nim games
    GameSpec("nim", NimGameParams, NimEngine, solvable=True),
    GameSpec("modified_nim", NoGameParams, ModifiedNimEngine, solvable=True),
    GameSpec("inverse_nim", NimGameParams, InverseNimEngine, solvable=True),
    GameSpec("story_nim", NimGameParams, StoryNimEngine, solvable=True),
    # connect 4
    GameSpec("connect_four", NoGameParams, ConnectFourEngine, solvable=False),
    # breakthrough
    GameSpec("breakthrough", NoGameParams, BreakthroughEngine, solvable=False),
]


def register_builtin_games(registry: Registry) -> None:
    for spec in _BUILTIN_GAMES:
        registry.register_game(spec)
