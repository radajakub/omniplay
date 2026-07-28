from __future__ import annotations

from omniplay.games.builtins import register_builtin_games
from omniplay.llm import LLM, LLMConfig
from omniplay.player.builtins import register_builtin_players
from omniplay.registry import Registry


class OmniPlay:
    """Central application object (`op`). Building one is the one-stop bootstrap: it creates the
    instance-scoped `op.registry` (no global state), registers the built-in games and players into it,
    and instantiates the LLM router (which the LLM players use). External code extends via
    `op.registry.register_game(...)` / `op.registry.register_player(...)`."""

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self._registry = Registry()
        self._llm = LLM(llm_config if llm_config is not None else LLMConfig.from_env())

        register_builtin_games(self._registry)
        register_builtin_players(self._registry, self._llm)

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def llm(self) -> LLM:
        return self._llm
