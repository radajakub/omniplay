"""The legacy migration transforms old result files into the new schema (ai->llm, os->metacentrum,
recomputed hashes/names, LLM extras folded into `data`) and aggregates per-opponent experiments; the
output loads back through the new ResultTracker/GameTracker."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from omniplay.app import OmniPlay
from omniplay.common.paths import BenchmarkPathBuilder
from omniplay.llm import LLMConfig
from omniplay.trackers.game_tracker import GameTracker

_spec = importlib.util.spec_from_file_location('migrate_legacy_results', Path(__file__).parent.parent / 'scripts' / 'migrate_legacy_results.py')
assert _spec is not None and _spec.loader is not None
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)

op = OmniPlay(LLMConfig())
registry = op.registry

# an old (os-hosted) LLM player vs a random baseline, in an opt-prefixed experiment
OLD_I = 'ai:actions:text:os:glm-5.2:thinking_enabled=True'
OLD_O = 'random:distribution=uniform'


def _write_old_matchup(source_results: Path) -> None:
    matchup = source_results / 'opt_commercial_ttt' / 'tic_tac_toe_100' / 'ai_actions_text_os_glm-5.2_thinking_enabled_True_random_uniform'
    matchup.mkdir(parents=True)
    (matchup / 'metadata.json').write_text(json.dumps({
        'experiment': 'opt_commercial_ttt', 'i_config': OLD_I, 'o_config': OLD_O,
        'game_config': 'tic_tac_toe:', 'n_games': 2, 'completed': [1, 2],
    }))
    old_game = {
        'game_round': 1, 'i_player': OLD_I, 'o_player': OLD_O,
        'instance_params': {}, 'other_params': {}, 'seq': 2,
        'steps': [
            {  # the LLM player's move: carries tokens + reasoning extras
                'seq': 1, 'player_name': 'AI ... glm-5.2', 'player_hash': 'old-ai-hash',
                'serialized_state': 'STATE_1', 'observation': 'OBS_1', 'move': '<C2R2>',
                'full_model_output': 'Action: <C2R2>', 'reasoning_trace': 'think about center',
                'system_message': 'sys', 'prompt_message': 'prompt', 'input_tokens': 332, 'output_tokens': 227,
            },
            {  # the random bot's move: no tokens, no extras
                'seq': 2, 'player_name': 'Random uniform', 'player_hash': 'old-rand-hash',
                'serialized_state': 'STATE_2', 'observation': 'OBS_2', 'move': '<C1R1>',
            },
        ],
        'ending': {'seq': 3, 'observation': 'OBS_END', 'result': 0},
    }
    (matchup / 'game_1.json').write_text(json.dumps(old_game))
    (matchup / 'game_2.json').write_text(json.dumps({**old_game, 'game_round': 2}))
    (matchup / 'recognition.json').write_text('{}')  # non-game file must be ignored


def test_config_string_remap():
    assert migrate.remap_config_string(OLD_I) == 'llm:actions:text:metacentrum:glm-5.2:thinking_enabled=True'
    assert migrate.remap_config_string(OLD_O) == OLD_O  # non-ai config untouched


def test_experiment_aggregation_names():
    assert migrate.merged_experiment('opt_commercial_ttt') == 'commercial_ttt'
    assert migrate.merged_experiment('rand_commercial_nim') == 'commercial_nim'
    assert migrate.merged_experiment('rand_ttt') == 'ttt'


def test_migration_produces_loadable_new_schema(tmp_path):
    source = tmp_path / 'old'
    dest = tmp_path / 'new'
    _write_old_matchup(source)

    report = migrate.run_migration(op, source, dest, dry_run=False)
    assert report['matchups'] == 1 and not report['errors']
    assert report['experiments']['commercial_ttt']['matchups'] == 1

    new_i = registry.player_config('llm:actions:text:metacentrum:glm-5.2:thinking_enabled=True')
    new_o = registry.player_config('random:distribution=uniform')
    game = registry.game_config('tic_tac_toe:')

    # the matchup lands under the aggregated experiment with new (llm/metacentrum) paths
    base = dest / 'results' / 'benchmarks' / 'commercial_ttt' / f'{game.path}_2' / f'{new_i.path}_{new_o.path}'
    assert (base / 'metadata.json').exists()

    metadata = json.loads((base / 'metadata.json').read_text())
    assert metadata['experiment'] == 'commercial_ttt'
    assert metadata['i_config'] == new_i.to_string() and metadata['o_config'] == new_o.to_string()

    # the game file loads back through the new package
    tracker = GameTracker.from_dict(json.loads((base / 'game_1.json').read_text()), registry)
    assert tracker.i_player.hash == new_i.hash and tracker.o_player.hash == new_o.hash

    llm_step, bot_step = tracker.steps
    # recomputed identity + LLM extras folded into `data`, tokens preserved
    assert llm_step.player_hash == new_i.hash and llm_step.player_name == new_i.to_string()
    assert llm_step.data == {'reasoning_trace': 'think about center', 'full_output': 'Action: <C2R2>', 'system_message': 'sys', 'prompt_message': 'prompt'}
    assert (llm_step.input_tokens, llm_step.output_tokens) == (332, 227)
    # the bot step has no token concept and no extras
    assert bot_step.player_hash == new_o.hash and bot_step.data is None
    assert bot_step.input_tokens is None


def test_migrated_tree_is_loadable_by_result_tracker(tmp_path, monkeypatch):
    source = tmp_path / 'old'
    _write_old_matchup(source)
    dest = tmp_path / 'new'
    migrate.run_migration(op, source, dest, dry_run=False)

    # the migration already writes <dest>/results/benchmarks, exactly where the path builder reads
    monkeypatch.chdir(dest)

    new_i = registry.player_config('llm:actions:text:metacentrum:glm-5.2:thinking_enabled=True')
    new_o = registry.player_config('random:distribution=uniform')
    game = registry.game_config('tic_tac_toe:')
    from omniplay.trackers.result_tracker import ResultTracker

    tracker = ResultTracker.new('commercial_ttt', new_i, new_o, game, 2, registry, path_builder=BenchmarkPathBuilder())
    tracker.load_if_exists()
    assert tracker.is_complete()
    assert all(gt is not None for gt in tracker.games)
