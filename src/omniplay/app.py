from __future__ import annotations

from omniplay.games.builtins import register_builtin_games
from omniplay.llm import LLM, LLMConfig
from omniplay.registry import Registry


class OmniPlay:
    """Central application object (`op`). Building one is the one-stop bootstrap: it creates the
    instance-scoped `op.registry` (no global state), registers the built-in games (and, from Phase 4,
    players) into it, and instantiates the LLM router. External code extends via
    `op.registry.register_game(...)` / `register_player(...)`."""

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self._registry = Registry()
        register_builtin_games(self._registry)
        self._llm = LLM(llm_config if llm_config is not None else LLMConfig.from_env())

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def llm(self) -> LLM:
        return self._llm
