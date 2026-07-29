# OmniPlay

OmniPlay is a benchmark suite for evaluating the performance of LLMs and LLM agents in simple,
fully-observable game environments. It pits players (LLMs, MCTS, optimal solvers, random, or human)
against each other across a matrix of games and records every step for later analysis.

**Live results** for a selection of models and games are available at
[omniplay.jakubrada.com](https://omniplay.jakubrada.com).

## Installation

```bash
pip install omniplay
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add omniplay
```

Requires Python 3.12+.

## Quickstart

Building an `OmniPlay` object is the one-stop bootstrap: it creates an instance-scoped registry,
registers the built-in games and players, and wires up the LLM router.

```python
import asyncio

from omniplay import OmniPlay
from omniplay.harness.benchmark import Benchmark

op = OmniPlay()  # reads provider keys from the environment (see Configuration)

benchmark = Benchmark(
    experiment="quickstart",
    op=op,
    game_configs=["tic_tac_toe:"],
    player_configs=["random:distribution=uniform"],
    opponent_configs=["optimal:stochastic=True"],
    num_games=10,
)

results = asyncio.run(benchmark.run())
```

Runs are **resumable** and written under `results/benchmarks/<experiment>/` in the current working
directory; re-running skips already-completed rounds.

### Config strings

Games and players are addressed by `name:key=value:key=value` strings, e.g.
`llm:actions:text:openai:gpt-5:thinking_enabled=True` or `random:distribution=uniform`.

**Built-in games:** `tic_tac_toe`, `modified_tic_tac_toe`, `magic_square`, `story_magic_square`,
`nim`, `modified_nim`, `inverse_nim`, `story_nim`, `connect_four`, `breakthrough`.

**Built-in players:** `human`, `random`, `mcts`, `optimal`, `llm`.

Extend either set at runtime via `op.registry.register_game(...)` / `op.registry.register_player(...)`.

## Configuration

LLM providers are configured through environment variables (a `.env` file is loaded automatically).
`OmniPlay()` self-disables any provider whose key is absent, so bot-only benchmarks run offline.
See [`.env.example`](.env.example):

```bash
OPENAI_API_KEY=...
OPENAI_ORGANIZATION=...
OPENAI_PROJECT=...

GEMINI_API_KEY=...
GEMINI_PROJECT=...

METACENTRUM_BASE_URL=...
METACENTRUM_API_KEY=...
```

## Extending OmniPlay

Games and players are **open registries** on `op.registry` — you can add your own from your own code
without modifying the package. Each is registered as a spec that pairs a config-string key with the
classes that implement it.

### Adding a player

Implement two things:

1. A `PlayerParams` subclass (`configs/player_params.py`) — the parsed form of your config string.
   Implement `from_string` / `to_string` / `path_suffix`. Reuse `NoGameParams`-style emptiness if your
   player is parameterless.
2. A `Player` subclass (`player/player.py`) — implement `initialize_policy` (one-time setup per game),
   the async `__call__` (given the game, an `InterfaceObservation`, and the legal `InterfaceAction`s,
   return a `PlayerOutput` — set `action=None` to forfeit), and `format_llm_output`.

Optionally, attach a `PlayerTracker` to persist extra per-step data onto each recorded `GameStep`.

Then register a `PlayerSpec`:

```python
from dataclasses import dataclass

from omniplay import OmniPlay
from omniplay.configs.player_config import PlayerConfig
from omniplay.configs.player_params import PlayerParams
from omniplay.core.game import TurnBasedGame
from omniplay.core.interface import InterfaceAction, InterfaceObservation
from omniplay.core.prompt_adapter import PromptAdapter
from omniplay.player.player import Player, PlayerIdentifier, PlayerOutput
from omniplay.player.spec import PlayerSpec


@dataclass(frozen=True, eq=True)
class FirstMoveParams(PlayerParams):
    @classmethod
    def from_string(cls, params_string: str) -> "FirstMoveParams":
        return cls()

    def to_string(self) -> str:
        return ""

    @property
    def path_suffix(self) -> str:
        return ""


class FirstMovePlayer(Player):
    def initialize_policy(self, game: TurnBasedGame, prompt_adapter_template: PromptAdapter) -> None:
        pass

    async def __call__(self, game: TurnBasedGame, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> PlayerOutput:
        return PlayerOutput(action=legal_moves[0] if legal_moves else None)

    def format_llm_output(self, player_output: PlayerOutput) -> str:
        return ""


op = OmniPlay()
op.registry.register_player(PlayerSpec("first", FirstMoveParams, lambda game, cfg, pid: FirstMovePlayer(cfg, pid)))
# usable anywhere as the config string "first:"
```

### Adding a game

Games are backed by [OpenSpiel](https://github.com/google-deepmind/open_spiel): the underlying game must
be loadable by `pyspiel.load_game(...)` (a built-in OpenSpiel game or a custom game you register with
OpenSpiel). A new variant implements the same set of classes the built-ins do — use any game under
[`src/omniplay/games/`](src/omniplay/games/) (e.g. `tic_tac_toe/tic_tac_toe.py`) as a template:

- **`TurnBasedGame`** — binds a registry `game_type` key to an OpenSpiel `game_name`.
- **`InterfaceTransformer`** — renders state/actions for both display and the LLM prompt.
- **`InterfaceAction`** / **`InterfaceObservation`** — convert to and from OpenSpiel (`from_openspiel` /
  `to_openspiel`).
- **`PromptAdapter`** — the game's head prompt and expected action format.
- **`TurnBasedEngine`** — wires all of the above together (`engine_factory: GameConfig -> TurnBasedEngine`).
- Optionally a **`GameParams`** subclass for parameterized variants (or reuse `NoGameParams`).

Then register a `GameSpec`:

```python
from omniplay.configs.game_params import NoGameParams
from omniplay.games.spec import GameSpec

op.registry.register_game(
    GameSpec(
        key="my_game",
        params_cls=NoGameParams,  # or a custom GameParams subclass
        engine_factory=MyGameEngine,  # GameConfig -> TurnBasedEngine
        solvable=False,  # True enables minimax optimality/regret analysis (small trees only)
    )
)
# usable anywhere as the config string "my_game:"
```

Registered games and players work everywhere the built-ins do — in `Benchmark`, the analysis pipeline,
and the scripts.

## Reproducing the paper results

The experiment scripts under [`scripts/`](scripts/) are **not** part of the installed package — they
are the tooling used to produce and reproduce the paper's results from a repository checkout. Use them
when you want to re-run the exact benchmarks the paper reports, extend them with new models, or run the
analysis and export pipelines on the resulting transcripts. Everything is resumable, so an interrupted
run continues where it left off.

The complete experiment definitions from the paper are prepared under
[`experiments/benchmarks/`](experiments/benchmarks/):

| Experiment         | File                | Games                                                                       |
| ------------------ | ------------------- | --------------------------------------------------------------------------- |
| Tic-tac-toe family | `ttt.json`          | `tic_tac_toe`, `modified_tic_tac_toe`, `magic_square`, `story_magic_square` |
| Nim family         | `nim.json`          | `nim`, `modified_nim`, `inverse_nim`, `story_nim`                           |
| Connect Four       | `connect_four.json` | `connect_four`                                                              |

Each file declares the full sweep — the LLM players, the opponents (`random`, `mcts`, `optimal`), and
the number of rounds — with per-item `enabled` toggles so you can narrow a run without editing the sweep.

```bash
git clone https://github.com/radajakub/omniplay.git
cd omniplay
uv sync

# run a prepared experiment (reads experiments/benchmarks/ttt.json)
uv run python scripts/run.py --experiment ttt

# or an ad-hoc smoke run
uv run python scripts/run.py --name smoke \
    --games tic_tac_toe: \
    --players random:distribution=uniform \
    --opponents optimal:stochastic=True \
    --num-games 10
```

The LLM matchups require the relevant provider API keys (see [Configuration](#configuration)) and will
incur API cost; bot-vs-bot matchups run offline. Results are written under
`results/benchmarks/<experiment>/`.

Then analyze or export the transcripts:

```bash
uv run python scripts/analyze.py --experiment ttt   # compute per-matchup statistics + confidence intervals
uv run python scripts/export.py --experiment ttt --out ttt.tar.gz   # export results for the OmniPlay website
uv run python scripts/play.py --game tic_tac_toe: --i human: --o optimal:stochastic=True  # play interactively
```

The full result set is large (tens of thousands of game transcripts) and is not stored in this
repository. <!-- TODO: link the archived dataset (Zenodo DOI / Hugging Face) once published. -->

## License

[MIT](LICENSE) © Jakub Rada
