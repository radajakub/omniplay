from __future__ import annotations

import time
from dataclasses import dataclass, field

from plybench.callbacks.benchmark_callbacks import BenchmarkCallbacks
from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.harness.results import BenchmarkResults
from plybench.observability.notifications import NotificationClient
from plybench.trackers.result_tracker import ResultTracker


def _format_duration(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


@dataclass
class _NotificationProgress:
    total_matchups: int = 0
    done_matchups: int = 0
    # rounds actually played this run (preexisting/resumed rounds excluded) — the throughput signal for the ETA
    fresh_rounds_total: int = 0
    fresh_rounds_done: int = 0
    start: float = 0.0
    preexisting: dict[tuple[str, str, str], set[int]] = field(default_factory=dict)


def notification_benchmark_callbacks(notif: NotificationClient, experiment: str) -> BenchmarkCallbacks:
    # push a notification as each matchup finishes and a final summary. matchups all share the per-provider
    # LLM-call semaphore and finish clustered near the end, so the ETA is derived from *round* throughput
    # (rounds drain through that pipe steadily) rather than from matchup completions.
    state = _NotificationProgress()

    def key(game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> tuple[str, str, str]:
        return (game_config.path, i.path, o.path)

    def on_benchmark_start(game_configs: list[str], player_configs: list[str], opponent_configs: list[str]) -> None:
        state.total_matchups = len(game_configs) * len(player_configs) * len(opponent_configs)
        state.done_matchups = 0
        state.fresh_rounds_total = 0
        state.fresh_rounds_done = 0
        state.start = time.monotonic()
        state.preexisting.clear()

    def on_matchup_start(result_tracker: ResultTracker, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> None:
        preexisting = set(result_tracker.get_completed_games())
        state.preexisting[key(game_config, i, o)] = preexisting
        state.fresh_rounds_total += result_tracker.n - len(preexisting)

    def on_round_complete(game_config: GameConfig, i: PlayerConfig, o: PlayerConfig, game_round: int) -> None:
        if game_round in state.preexisting.get(key(game_config, i, o), set()):
            return  # resumed round — completes instantly, must not inflate the throughput estimate
        state.fresh_rounds_done += 1

    def on_matchup_end(result_tracker: ResultTracker) -> None:
        state.done_matchups += 1
        remaining = max(state.total_matchups - state.done_matchups, 0)
        elapsed = time.monotonic() - state.start
        label = f"{result_tracker.game.path}: {result_tracker.i.path} vs {result_tracker.o.path}"
        parts = [f"[{experiment}] matchup done ({state.done_matchups}/{state.total_matchups}, {remaining} left): {label}", f"elapsed {_format_duration(elapsed)}"]
        rounds_left = state.fresh_rounds_total - state.fresh_rounds_done
        if rounds_left > 0 and state.fresh_rounds_done > 0 and elapsed > 0:
            eta = rounds_left / (state.fresh_rounds_done / elapsed)
            parts.append(f"est. {_format_duration(eta)} left")
        if state.fresh_rounds_total:
            parts.append(f"{state.fresh_rounds_done}/{state.fresh_rounds_total} rounds done")
        notif.notify(" | ".join(parts))

    def on_benchmark_end(results: BenchmarkResults) -> None:
        complete = sum(1 for tracker in results.trackers if tracker.is_complete())
        elapsed = time.monotonic() - state.start
        notif.notify(f"[{experiment}] benchmark finished: {complete}/{len(results.trackers)} matchups complete in {_format_duration(elapsed)}")

    return BenchmarkCallbacks(
        benchmark_start_callback=on_benchmark_start,
        matchup_start_callback=on_matchup_start,
        round_complete_callback=on_round_complete,
        matchup_end_callback=on_matchup_end,
        benchmark_end_callback=on_benchmark_end,
    )
