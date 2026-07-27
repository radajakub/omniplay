from __future__ import annotations

from omniplay.llm import LLM, LLMConfig


class OmniPlay:
    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self._llm = LLM(llm_config if llm_config is not None else LLMConfig.from_env())

    @property
    def llm(self) -> LLM:
        return self._llm
