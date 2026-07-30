from __future__ import annotations

import asyncio
import uuid

from plybench.app import PlyBench
from plybench.callbacks.benchmark_callbacks import BenchmarkCallbacks
from plybench.callbacks.game_callbacks import GameCallbacks
from plybench.common.paths import BenchmarkPathBuilder, ExperimentPathBuilder
from plybench.configs.game_config import GameConfig
from plybench.configs.matchup import Matchup
from plybench.configs.player_config import PlayerConfig
from plybench.player.player import Player
from plybench.trackers.result_tracker import ResultTracker


def first_starts(game_round: int, num_games: int) -> bool:
    return game_round <= (num_games // 2)


def order_players_for_game(i: Player, o: Player, game_round: int, num_games: int) -> tuple[Player, Player]:
    # colour balancing: the first half of the rounds the i-player moves first, the second half the o-player does
    return (i, o) if first_starts(game_round, num_games) else (o, i)


async def _play_round(
    op: PlyBench,
    matchup: Matchup,
    game_round: int,
    result_tracker: ResultTracker,
    game_callbacks: GameCallbacks | None,
    benchmark_callbacks: BenchmarkCallbacks,
) -> None:
    if result_tracker.is_game_complete(game_round):
        benchmark_callbacks.on_round_complete(matchup.game, matchup.i, matchup.o, game_round)
        return

    benchmark_callbacks.on_round_start(matchup.game, matchup.i, matchup.o, game_round)

    engine = op.registry.build_engine(matchup.game)
    player_i = op.registry.build_player(engine.game, matchup.i, "i")
    player_o = op.registry.build_player(engine.game, matchup.o, "o")

    player_pair = order_players_for_game(player_i, player_o, game_round, matchup.num_games)
    game_tracker = await engine.play(player_pair, game_callbacks=game_callbacks, game_round=game_round)

    result_tracker.record_game(game_round, game_tracker)
    benchmark_callbacks.on_round_complete(matchup.game, matchup.i, matchup.o, game_round)


async def run_matchup(
    op: PlyBench,
    matchup: Matchup,
    game_callbacks: GameCallbacks | None = None,
    benchmark_callbacks: BenchmarkCallbacks | None = None,
    path_builder: ExperimentPathBuilder | None = None,
    experiment: str | None = None,
    save_on_record: bool = True,
    max_concurrent: int | None = None,
) -> ResultTracker:
    benchmark_callbacks = benchmark_callbacks if benchmark_callbacks is not None else BenchmarkCallbacks()
    experiment = experiment if experiment is not None else f"run_{uuid.uuid4().hex}"
    path_builder = path_builder if path_builder is not None else BenchmarkPathBuilder()

    result_tracker = ResultTracker.new(
        experiment,
        matchup.i,
        matchup.o,
        matchup.game,
        matchup.num_games,
        op.registry,
        path_builder=path_builder,
        save_on_record=save_on_record,
    )
    result_tracker.load_if_exists()

    benchmark_callbacks.on_matchup_start(result_tracker, matchup.game, matchup.i, matchup.o)

    if result_tracker.is_complete():
        benchmark_callbacks.on_matchup_end(result_tracker)
        return result_tracker

    missing_games = result_tracker.get_missing_games()
    semaphore = asyncio.Semaphore(max_concurrent if max_concurrent is not None else len(missing_games))

    async def _run_round(game_round: int) -> None:
        async with semaphore:
            await _play_round(op, matchup, game_round, result_tracker, game_callbacks, benchmark_callbacks)

    await asyncio.gather(*(asyncio.create_task(_run_round(game_round)) for game_round in missing_games))

    benchmark_callbacks.on_matchup_end(result_tracker)
    return result_tracker


async def single_game(
    op: PlyBench,
    game_config: GameConfig,
    i_config: PlayerConfig,
    o_config: PlayerConfig,
    game_callbacks: GameCallbacks | None = None,
    benchmark_callbacks: BenchmarkCallbacks | None = None,
) -> ResultTracker:
    return await run_matchup(
        op,
        Matchup(game_config, i_config, o_config, 1),
        game_callbacks=game_callbacks,
        benchmark_callbacks=benchmark_callbacks,
        save_on_record=False,
    )
