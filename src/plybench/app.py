from __future__ import annotations

from plybench.games.builtins import register_builtin_games
from plybench.llm import LLM, LLMConfig
from plybench.observability.notifications import NotificationClient
from plybench.player.builtins import register_builtin_players
from plybench.registry import Registry


class PlyBench:
    def __init__(self, llm_config: LLMConfig | None = None, hf_models: list[str] | None = None, notif_enabled: bool = False) -> None:
        self._registry = Registry()
        # hf_models declares which local HuggingFace models this environment uses; it feeds the
        # default env config only (an explicit llm_config already carries its own huggingface setup)
        config = llm_config if llm_config is not None else LLMConfig.from_env(huggingface_models=hf_models)
        self._llm = LLM(config)
        # download/verify any provider-local resources (e.g. HuggingFace models) up front
        self._llm.bootstrap()

        self._notification_client = NotificationClient.from_env(enabled=notif_enabled)

        register_builtin_games(self._registry)
        register_builtin_players(self._registry, self._llm)

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def llm(self) -> LLM:
        return self._llm

    @property
    def notif(self) -> NotificationClient:
        return self._notification_client
