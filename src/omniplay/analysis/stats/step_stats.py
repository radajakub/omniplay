from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omniplay.common.enums import StateClass


@dataclass(frozen=True)
class StepStats:
    """Per-move analysis record produced by replaying a recorded game against the solved minimax cache:
    the move's optimality and regret plus how forced the state was (state_class) and its token cost."""

    seq: int
    input_tokens: int | None
    output_tokens: int | None
    state_class: StateClass
    is_optimal: bool
    regret: float

    @property
    def is_trivial(self) -> bool:
        return self.state_class.is_forced

    def to_dict(self) -> dict[str, Any]:
        return {
            'seq': self.seq,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'state_class': self.state_class.value,
            'is_optimal': self.is_optimal,
            'regret': self.regret,
        }
