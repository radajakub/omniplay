# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0]

### Added

- HuggingFace provider that runs models locally (downloading them to the HuggingFace cache) and
  exposes embeddings through `LLM.embed`. Declare the environment's models with
  `OmniPlay(hf_models=[...])`; they are downloaded/verified at bootstrap, and requesting a model
  that was not bootstrapped raises a helpful error. Reads `HF_TOKEN` for gated/private models.
  Ships one supported model: `sup-simcse-bert` (`princeton-nlp/sup-simcse-bert-base-uncased`).

### Changed

- Each LLM provider SDK is now an optional extra (`openai`, `gemini`, `metacentrum`,
  `huggingface`, and `all`); the core install no longer pulls in provider SDKs. The router wires
  up only the providers whose dependency is installed (and configured).

## [1.0.0]

Initial release.

- Benchmark harness for LLMs, MCTS, optimal solvers, random, and human players.
- Built-in games: tic-tac-toe family, nim family, connect four, breakthrough.
- Analysis pipeline with confidence intervals and minimax-based optimality/regret.
- Open registries for adding custom games and players.

[Unreleased]: https://github.com/radajakub/omniplay/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/radajakub/omniplay/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/radajakub/omniplay/releases/tag/v1.0.0
