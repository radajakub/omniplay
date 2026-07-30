from __future__ import annotations

import re

from pydantic import BaseModel, Field

from plybench.common.enums import OutputStrategies
from plybench.core.output_strategy import OutputStrategy, OutputStrategyExtractionResult

_TEXT_PROMPT = """
You must choose a legal action.

Your output must be in the following format:

Action: {action_format}

Please return your answer with the action only, no explanation.
"""

_STRUCTURED_PROMPT = """
You must choose a legal action.

Your output must be in the following format:

{action_format}

Please return your answer with the action only, no explanation.
"""


def _normalize_action(action: str | None) -> str | None:
    if not action:
        return None
    action = action.strip().strip("<>").strip()
    return f"<{action}>" if action else None


class TextStrategy(OutputStrategy):
    def output_prompt(self, action_format: str) -> str:
        return _TEXT_PROMPT.format(action_format=action_format)

    def get_output_schema(self) -> type[BaseModel] | None:
        return None

    def extract(self, llm_response: str) -> OutputStrategyExtractionResult:
        text = llm_response.strip()
        if not text:
            return OutputStrategyExtractionResult()
        # take the last non-empty line, dropping an optional "Action:" label
        line = text.splitlines()[-1].strip()
        line = re.sub(r"^Action:\s*", "", line).strip()
        return OutputStrategyExtractionResult(action=_normalize_action(line))


class ActionSchema(BaseModel):
    action: str = Field(description="The action to play in the next turn")


class StructuredOutputStrategy(OutputStrategy):
    def output_prompt(self, action_format: str) -> str:
        return _STRUCTURED_PROMPT.format(action_format=action_format)

    def get_output_schema(self) -> type[BaseModel] | None:
        return ActionSchema

    def extract(self, llm_response: str) -> OutputStrategyExtractionResult:
        parsed = ActionSchema.model_validate_json(llm_response)
        return OutputStrategyExtractionResult(action=_normalize_action(parsed.action))


def build_output_strategy(strategy: OutputStrategies) -> OutputStrategy:
    match strategy:
        case OutputStrategies.TEXT:
            return TextStrategy()
        case OutputStrategies.STRUCTURED:
            return StructuredOutputStrategy()
