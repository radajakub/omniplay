"""One-off migration of the original repo's benchmark result files into the new omniplay schema, while
aggregating the per-opponent experiments into one experiment per game family.

Only the RAW results are migrated; the old `analysis/` tree is not copied (stats are recomputed from the
results on demand). Alongside the results the migration reconstructs each experiment's benchmark config at
`<dest>/experiments/benchmarks/<name>.json` (every migrated axis toggled on) so the result tree is
immediately re-runnable / analysable via `Benchmark.load_experiment`.

It is NON-DESTRUCTIVE: it reads the old `results/benchmarks/` tree and writes a fresh tree under
`--dest`; the source is never modified. Run with `--dry-run` first to preview the plan.

Transforms applied per matchup:
  * config strings: `ai:` -> `llm:`, provider `os` -> `metacentrum`, then re-parsed through the new
    registry so serialization / hash / path are canonical (other configs pass through unchanged);
  * GameStep: `player_name` = new `to_string()`, `player_hash` = new sha256; old flat LLM fields
    (`full_model_output`/`reasoning_trace`/`system_message`/`prompt_message`) fold into `data`;
  * experiments: the leading opponent prefix (`opt_`/`mcts_`/`rand_`) and a `commercial_` token are
    stripped so per-opponent experiments merge into one experiment per game family (`ttt`/`nim`/
    `connect_four`); the `<player>_<opponent>` matchup dir keeps individual matchups distinct.

Usage:
    uv run python scripts/migrate_legacy_results.py --source ../omniplay --dest ./migrated --dry-run
    uv run python scripts/migrate_legacy_results.py --source ../omniplay --dest ./migrated
Output lands under `<dest>/results/benchmarks/`; run the new package with `<dest>` as the cwd.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from omniplay.app import OmniPlay
from omniplay.common.enums import GameResults
from omniplay.configs.benchmark_config import BenchmarkConfig, ToggleItem
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.llm import LLMConfig
from omniplay.trackers.game_tracker import GameEnding, GameStep, GameTracker


class MatchupAxes(NamedTuple):
    """The canonical (destination + axis) info for one migrated matchup, used both for collision
    detection and to reconstruct the per-experiment benchmark config file."""

    dest: Path
    game: str
    player: str
    opponent: str
    num_games: int

OPPONENT_PREFIXES = ('opt', 'mcts', 'rand')
PROVIDER_REMAP = {'os': 'metacentrum'}
# old flat GameStep field -> key inside the new GameStep `data` dict (mirrors LLMPlayerTracker.record)
DATA_FIELDS = (('reasoning_trace', 'reasoning_trace'), ('full_model_output', 'full_output'), ('system_message', 'system_message'), ('prompt_message', 'prompt_message'))


def remap_config_string(old: str) -> str:
    key, _, rest = old.partition(':')
    if key != 'ai':
        return old
    parts = rest.split(':')  # <observation>:<strategy>:<provider>:<model>:<options>
    if len(parts) >= 3:
        parts[2] = PROVIDER_REMAP.get(parts[2], parts[2])
    return 'llm:' + ':'.join(parts)


def migrate_config(op: OmniPlay, old: str) -> PlayerConfig:
    return op.registry.player_config(remap_config_string(old))


def merged_experiment(name: str) -> str:
    head, sep, tail = name.partition('_')
    if sep and head in OPPONENT_PREFIXES:
        name = tail
    return name.removeprefix('commercial_')


def _step_data(old_step: dict) -> dict[str, str]:
    return {new_key: old_step[old_key] for old_key, new_key in DATA_FIELDS if old_step.get(old_key)}


def migrate_step(old_step: dict, new_i: PlayerConfig, new_o: PlayerConfig, i_old_hash: str | None) -> GameStep:
    player = new_i if old_step['player_hash'] == i_old_hash else new_o
    data = _step_data(old_step)
    return GameStep(
        old_step['seq'], player.to_string(), player.hash,
        old_step['serialized_state'], old_step['observation'], old_step['move'],
        input_tokens=old_step.get('input_tokens'),
        output_tokens=old_step.get('output_tokens'),
        reasoning_tokens=old_step.get('reasoning_tokens'),
        data=data or None,
    )


def migrate_game_tracker(op: OmniPlay, old_game: dict) -> GameTracker:
    # each game keeps its OWN first mover as i_player (results are recorded from that POV); legacy
    # matchups alternate starters, so this is not always the matchup's model — the model/opponent
    # identity lives in the tracker metadata, and the analysis inverts per game as needed.
    game_i = migrate_config(op, old_game['i_player'])
    game_o = migrate_config(op, old_game['o_player'])

    old_steps = old_game.get('steps') or []
    i_old_hash = old_steps[0]['player_hash'] if old_steps else None  # first recorded step = i_player
    steps = [migrate_step(step, game_i, game_o, i_old_hash) for step in old_steps]

    ending = None
    if old_game.get('ending'):
        end = old_game['ending']
        ending = GameEnding(end['seq'], end['observation'], GameResults.from_value(end['result']))

    return GameTracker(
        int(old_game['game_round']), game_i, game_o, old_game.get('instance_params', {}),
        steps, ending, int(old_game.get('seq', 0)), old_game.get('other_params', {}),
    )


def _matchup_dest(dest_root: Path, experiment: str, game: GameConfig, new_i: PlayerConfig, new_o: PlayerConfig, n_games: int) -> Path:
    # mirrors BenchmarkPathBuilder.game_base: <cwd>/results/benchmarks/<experiment>/<game>_<n>/<i>_<o>
    return dest_root / 'results' / 'benchmarks' / experiment / f'{game.path}_{n_games}' / f'{new_i.path}_{new_o.path}'


def migrate_matchup(op: OmniPlay, src_dir: Path, dest_root: Path, experiment: str, dry_run: bool) -> MatchupAxes:
    metadata = json.loads((src_dir / 'metadata.json').read_text())
    new_i = migrate_config(op, metadata['i_config'])
    new_o = migrate_config(op, metadata['o_config'])
    game = op.registry.game_config(metadata['game_config'])
    n_games = int(metadata['n_games'])

    dest = _matchup_dest(dest_root, experiment, game, new_i, new_o, n_games)
    axes = MatchupAxes(dest, game.to_string(), new_i.to_string(), new_o.to_string(), n_games)
    if dry_run:
        return axes

    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'metadata.json').write_text(json.dumps({
        'experiment': experiment,
        'i_config': new_i.to_string(),
        'o_config': new_o.to_string(),
        'game_config': game.to_string(),
        'n_games': n_games,
        'completed': list(metadata['completed']),
    }))
    for game_file in sorted(src_dir.glob('game_*.json')):
        tracker = migrate_game_tracker(op, json.loads(game_file.read_text()))
        (dest / game_file.name).write_text(json.dumps(tracker.to_dict()))
    return axes


def iter_matchups(source_results: Path) -> Iterator[tuple[str, Path]]:
    for experiment_dir in sorted(p for p in source_results.iterdir() if p.is_dir()):
        for game_dir in sorted(p for p in experiment_dir.iterdir() if p.is_dir()):
            for matchup_dir in sorted(p for p in game_dir.iterdir() if p.is_dir()):
                if (matchup_dir / 'metadata.json').exists():
                    yield experiment_dir.name, matchup_dir


def _new_group() -> dict:
    return {'sources': set(), 'matchups': 0, 'games': set(), 'players': set(), 'opponents': set(), 'num_games': Counter()}


def _experiment_config(group: dict) -> BenchmarkConfig:
    # every migrated matchup is a matrix cell we want re-runnable, so all axes are toggled on
    return BenchmarkConfig(
        [ToggleItem(value, True) for value in sorted(group['games'])],
        [ToggleItem(value, True) for value in sorted(group['players'])],
        [ToggleItem(value, True) for value in sorted(group['opponents'])],
        group['num_games'].most_common(1)[0][0],
    )


def _write_experiment_configs(dest_root: Path, experiments: dict, report: dict) -> None:
    config_dir = dest_root / 'experiments' / 'benchmarks'
    config_dir.mkdir(parents=True, exist_ok=True)
    for name, group in experiments.items():
        if len(group['num_games']) > 1:  # BenchmarkConfig holds a single num_games (matchup dirs keep their own <game>_<n>)
            report['errors'].append((name, f'mixed num_games {dict(group["num_games"])}, config uses {group["num_games"].most_common(1)[0][0]}'))
        (config_dir / f'{name}.json').write_text(json.dumps(_experiment_config(group).to_dict(), indent=2))


def run_migration(op: OmniPlay, source_results: Path, dest_root: Path, dry_run: bool = False) -> dict:
    report: dict = {'experiments': {}, 'matchups': 0, 'errors': []}
    seen: dict[Path, str] = {}

    for exp_name, matchup_dir in iter_matchups(source_results):
        merged = merged_experiment(exp_name)
        try:
            axes = migrate_matchup(op, matchup_dir, dest_root, merged, dry_run)
        except Exception as error:  # noqa: BLE001 - surface the offending matchup, keep going
            report['errors'].append((str(matchup_dir), repr(error)))
            continue

        if axes.dest in seen and seen[axes.dest] != str(matchup_dir):
            report['errors'].append((str(matchup_dir), f'destination collision with {seen[axes.dest]}'))
            continue
        seen[axes.dest] = str(matchup_dir)

        group = report['experiments'].setdefault(merged, _new_group())
        group['sources'].add(exp_name)
        group['matchups'] += 1
        group['games'].add(axes.game)
        group['players'].add(axes.player)
        group['opponents'].add(axes.opponent)
        group['num_games'][axes.num_games] += 1
        report['matchups'] += 1

    if not dry_run:
        _write_experiment_configs(dest_root, report['experiments'], report)

    return report


def _print_report(report: dict, dry_run: bool) -> None:
    prefix = '[dry-run] ' if dry_run else ''
    print(f'{prefix}migrated {report["matchups"]} matchups into {len(report["experiments"])} experiments:')
    for experiment, group in sorted(report['experiments'].items()):
        print(f'  {experiment}: {group["matchups"]} matchups, {len(group["players"])} players x {len(group["opponents"])} opponents x {len(group["games"])} games  <- {", ".join(sorted(group["sources"]))}')
    if not dry_run and report['experiments']:
        print(f'wrote {len(report["experiments"])} experiment config(s) to experiments/benchmarks/')
    for path, error in report['errors']:
        print(f'  ERROR {path}: {error}')


def _resolve_source_results(source: Path) -> Path:
    for candidate in (source, source / 'results' / 'benchmarks', source / 'benchmarks'):
        if candidate.is_dir() and any(candidate.glob('*/*/*/metadata.json')):
            return candidate
    raise SystemExit(f'no results/benchmarks tree found under {source}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='old repo root (or its results/benchmarks dir)')
    parser.add_argument('--dest', type=Path, default=Path('migrated'), help='output root; results land under <dest>/benchmarks')
    parser.add_argument('--dry-run', action='store_true', help='report the plan without writing anything')
    args = parser.parse_args()

    op = OmniPlay(LLMConfig())  # offline: only the registry is used, to parse/canonicalize configs
    report = run_migration(op, _resolve_source_results(args.source), args.dest, args.dry_run)
    _print_report(report, args.dry_run)


if __name__ == '__main__':
    main()
