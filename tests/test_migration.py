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
    # opponent prefix and the `commercial_` token both drop -> one experiment per game family
    assert migrate.merged_experiment('opt_commercial_ttt') == 'ttt'
    assert migrate.merged_experiment('rand_commercial_nim') == 'nim'
    assert migrate.merged_experiment('mcts_commercial_connect_four') == 'connect_four'
    assert migrate.merged_experiment('rand_ttt') == 'ttt'  # rand baseline merges into the same family


def test_migration_produces_loadable_new_schema(tmp_path):
    source = tmp_path / 'old'
    dest = tmp_path / 'new'
    _write_old_matchup(source)

    report = migrate.run_migration(op, source, dest, dry_run=False)
    assert report['matchups'] == 1 and not report['errors']
    assert report['experiments']['ttt']['matchups'] == 1

    new_i = registry.player_config('llm:actions:text:metacentrum:glm-5.2:thinking_enabled=True')
    new_o = registry.player_config('random:distribution=uniform')
    game = registry.game_config('tic_tac_toe:')

    # the matchup lands under the aggregated experiment with new (llm/metacentrum) paths
    base = dest / 'results' / 'benchmarks' / 'ttt' / f'{game.path}_2' / f'{new_i.path}_{new_o.path}'
    assert (base / 'metadata.json').exists()

    metadata = json.loads((base / 'metadata.json').read_text())
    assert metadata['experiment'] == 'ttt'
    assert metadata['i_config'] == new_i.to_string() and metadata['o_config'] == new_o.to_string()

    # the game file loads back through the new package
    tracker = GameTracker.from_dict(json.loads((base / 'game_1.json').read_text()), registry)
    assert tracker.i_player.hash == new_i.hash and tracker.o_player.hash == new_o.hash

    # a re-runnable benchmark config was reconstructed for the aggregated experiment
    from omniplay.configs.benchmark_config import BenchmarkConfig
    config_path = dest / 'experiments' / 'benchmarks' / 'ttt.json'
    assert config_path.exists()
    config = BenchmarkConfig.from_dict(json.loads(config_path.read_text()))
    assert config.num_games == 2
    assert config.get_game_configs() == [game.to_string()]
    assert config.get_player_configs() == [new_i.to_string()]
    assert config.get_opponent_configs() == [new_o.to_string()]

    llm_step, bot_step = tracker.steps
    # recomputed identity + LLM extras folded into `data`, tokens preserved
    assert llm_step.player_hash == new_i.hash and llm_step.player_name == new_i.to_string()
    assert llm_step.data == {'reasoning_trace': 'think about center', 'full_output': 'Action: <C2R2>', 'system_message': 'sys', 'prompt_message': 'prompt'}
    assert (llm_step.input_tokens, llm_step.output_tokens) == (332, 227)
    # the bot step has no token concept and no extras
    assert bot_step.player_hash == new_o.hash and bot_step.data is None
    assert bot_step.input_tokens is None


def test_opponent_first_game_keeps_its_own_perspective():
    # a legacy game where the OPPONENT moved first: its i_player is the opponent and the recorded
    # result is from the opponent's POV. Migration must preserve that (not force the matchup model as
    # i), otherwise the two players' moves/outcome get swapped for every opponent-started game.
    from omniplay.common.enums import GameResults

    old_game = {
        'game_round': 1, 'i_player': OLD_O, 'o_player': OLD_I,
        'instance_params': {}, 'other_params': {}, 'seq': 2,
        'steps': [
            {'seq': 1, 'player_name': 'Random uniform', 'player_hash': 'old-rand-hash',
             'serialized_state': 'S1', 'observation': 'O1', 'move': '<C1R1>'},
            {'seq': 2, 'player_name': 'AI ... glm-5.2', 'player_hash': 'old-ai-hash',
             'serialized_state': 'S2', 'observation': 'O2', 'move': '<C2R2>'},
        ],
        'ending': {'seq': 3, 'observation': 'OBS_END', 'result': 0},  # WIN from i_player (opponent) POV
    }
    new_i = registry.player_config('llm:actions:text:metacentrum:glm-5.2:thinking_enabled=True')
    new_o = registry.player_config('random:distribution=uniform')

    tracker = migrate.migrate_game_tracker(op, old_game)

    # the game keeps the opponent (random) as its own first-mover i_player, model as o_player
    assert tracker.i_player.hash == new_o.hash and tracker.o_player.hash == new_i.hash
    assert tracker.steps[0].player_hash == new_o.hash and tracker.steps[1].player_hash == new_i.hash
    # from the MODEL's POV the opponent's WIN inverts to a LOSS (the model was second and lost)
    assert tracker.get_result(new_i) == GameResults.LOSS
    assert tracker.get_result(new_o) == GameResults.WIN


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

    tracker = ResultTracker.new('ttt', new_i, new_o, game, 2, registry, path_builder=BenchmarkPathBuilder())
    tracker.load_if_exists()
    assert tracker.is_complete()
    assert all(gt is not None for gt in tracker.games)

    # the generated config drives Benchmark.load_experiment (reads experiments/benchmarks/ttt.json)
    from omniplay.harness.benchmark import Benchmark
    benchmark = Benchmark.load_experiment(op, 'ttt')
    assert benchmark.game_configs == [game.to_string()]
    assert benchmark.player_configs == [new_i.to_string()]
    assert benchmark.opponent_configs == [new_o.to_string()]
    assert benchmark.num_games == 2
