# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0]

### Added

- Grok provider (xAI) behind the `grok` extra, reusing the OpenAI-compatible endpoint. Reads
  `GROK_API_KEY` and the optional `GROK_BASE_URL` (defaults to `https://api.x.ai/v1`). Ships
  `grok-4.5`, `grok-4.3` and `grok-4.20-reasoning`.
- Anthropic Claude provider behind the `anthropic` extra (also included in `all`), reading
  `CLAUDE_API_KEY`. Ships `claude-fable-5`, `claude-opus-5`, `claude-opus-4.8`, `claude-sonnet-5`,
  `claude-sonnet-4.6` and `claude-haiku-4.5`, mapping reasoning effort onto Anthropic's thinking
  budget (with a numeric budget for models that take no effort parameter).
- Progress notifications through [ntfy.sh](https://ntfy.sh): `NotificationClient` reads `NTFY_URL`
  and `NTFY_TOKEN`, is exposed as `PlyBench.notif` and enabled with `PlyBench(notif_enabled=True)`.
  `scripts/run.py --notify` pushes a message per finished matchup — elapsed time, rounds completed
  and an ETA derived from round throughput — plus a final summary. Send failures are logged as
  warnings instead of interrupting the run.
- Console progress logging during a benchmark: per-matchup start/end plus a running `done/total`
  round counter that skips rounds resumed from an earlier run.
- `max` reasoning effort, and `kimi-k3` on the Metacentrum provider (replacing `kimi-k2.5`).
- The Grok, Claude and Kimi K3 models in the prepared `ttt`, `nim` and `connect_four` experiments.
- `scripts/play.py` prints the player's reasoning trace when one is available.

### Changed

- `console_benchmark_callbacks` moved from `plybench.callbacks.benchmark_callbacks` to
  `plybench.callbacks.console_callbacks`.
- `requests` is now a runtime dependency (used by the notification client).

### Removed

- `plybench.harness` no longer re-exports `Benchmark`, `run_matchup`, `single_game` and
  `order_players_for_game`; import them from `plybench.harness.benchmark` and
  `plybench.harness.matchup` instead.

## [1.0.0]

Initial release of PlyBench.

- Benchmark harness for LLMs, MCTS, optimal solvers, random, and human players.
- Built-in games: tic-tac-toe family, nim family, connect four, breakthrough.
- Analysis pipeline with confidence intervals and minimax-based optimality/regret.
- Open registries for adding custom games and players.
- LLM providers as optional extras (`openai`, `gemini`, `metacentrum`, `huggingface`, and
  `all`); the core install pulls in no provider SDKs, and the router wires up only the providers
  whose dependency is installed (and configured).
- HuggingFace provider that runs models locally (downloading them to the HuggingFace cache) and
  exposes embeddings through `LLM.embed`. Declare the environment's models with
  `PlyBench(hf_models=[...])`; they are downloaded/verified at bootstrap, and requesting a model
  that was not bootstrapped raises a helpful error. Reads `HF_TOKEN` for gated/private models.
  Ships one supported model: `sup-simcse-bert` (`princeton-nlp/sup-simcse-bert-base-uncased`).

[Unreleased]: https://github.com/radajakub/plybench/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/radajakub/plybench/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/radajakub/plybench/releases/tag/v1.0.0
