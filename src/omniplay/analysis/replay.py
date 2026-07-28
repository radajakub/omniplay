from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

from omniplay.analysis.stats.step_stats import StepStats
from omniplay.common.enums import StateClass
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.core.engine import TurnBasedEngine
from omniplay.player.simple.optimal_player import Judgeable
from omniplay.registry import Registry
from omniplay.trackers.game_tracker import GameStep, GameTracker


@dataclass
class _JudgedStep:
    step: GameStep
    state_class: StateClass
    is_optimal: bool
    regret: float


class TurnBasedReplayer:
    """Re-walks a recorded game and judges each of the analysed player's moves against the solved
    minimax cache, yielding per-move quality (optimality + regret). Generic across games — everything
    game-specific comes from the engine it is built with."""

    def __init__(self, engine: TurnBasedEngine, judge: Judgeable) -> None:
        self._engine = engine
        self._judge = judge

    def _iter_judged_steps(self, game_tracker: GameTracker, player_config: PlayerConfig) -> Iterator[_JudgedStep]:
        game = self._engine.game
        loss_value = float(game.get_reward_range()[0])

        for step in game_tracker.steps:
            game.deserialize_state(step.serialized_state)
            if step.player_hash != player_config.hash:
                continue

            pid = game.get_player()
            observation = self._engine.observation_class.from_openspiel(game.get_observation(pid), self._engine.interface_transformer)
            moves = [self._engine.action_class.from_openspiel(move, self._engine.interface_transformer) for move in game.get_legal_moves(pid)]

            verdict = self._judge.optimal(pid, observation)
            if verdict is None:
                raise ValueError(f'No judge verdict for player {pid} at state {observation.os_observation.state}')

            state_class = verdict.classify_state([move.number for move in moves], loss_value)

            if 'FAIL' in step.move:
                # a failed (illegal / malformed) move: worst-case regret, definitely not optimal
                is_optimal = False
                regret = float(verdict.V() - loss_value)
            else:
                selected = next((move for move in moves if move.to_llm().string == step.move), None)
                if selected is None:
                    raise ValueError(f'Recorded move not found among legal moves: {step.move}')
                is_optimal = bool(verdict.check_optimal(selected.number))
                regret = float(verdict.V() - verdict.Q(selected.number))

            yield _JudgedStep(step, state_class, is_optimal, regret)

    def replay_steps(self, game_tracker: GameTracker, player_config: PlayerConfig) -> list[StepStats]:
        return [
            StepStats(js.step.seq, js.step.input_tokens, js.step.output_tokens, js.state_class, js.is_optimal, js.regret)
            for js in self._iter_judged_steps(game_tracker, player_config)
        ]


def build_replayer(registry: Registry, game_config: GameConfig) -> TurnBasedReplayer:
    """Build a replayer for a (solvable) game: a fresh engine plus an optimal judge whose minimax cache
    is solved/loaded on initialize_policy. Only meaningful for `registry.solvable(game_config.key)`."""
    engine = registry.build_engine(game_config)
    judge = registry.build_player(engine.game, registry.player_config('optimal:'), 'i')
    judge.initialize_policy(engine.game, engine.prompt_adapter)
    return TurnBasedReplayer(engine, cast(Judgeable, judge))


class MemoizedReplay:
    """Caches replayed StepStats per game object so the optimality/regret extractors (which each iterate
    the same games) judge every game only once."""

    def __init__(self, replayer: TurnBasedReplayer, player_config: PlayerConfig) -> None:
        self._replayer = replayer
        self._player = player_config
        self._cache: dict[int, list[StepStats]] = {}

    def __call__(self, game_tracker: GameTracker) -> list[StepStats]:
        key = id(game_tracker)
        if key not in self._cache:
            self._cache[key] = self._replayer.replay_steps(game_tracker, self._player)
        return self._cache[key]
