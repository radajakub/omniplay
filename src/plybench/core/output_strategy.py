from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class OutputStrategyExtractionResult:
    action: str | None = None


class OutputStrategy(ABC):
    @abstractmethod
    def output_prompt(self, action_format: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_output_schema(self) -> type[BaseModel] | None:
        raise NotImplementedError

    @abstractmethod
    def extract(self, llm_response: str) -> OutputStrategyExtractionResult:
        raise NotImplementedError
