from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omniplay.common.serializable import Serializable
from omniplay.utils.text import to_bool


@dataclass(frozen=True, eq=True)
class ToggleItem(Serializable):
    value: str
    enabled: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToggleItem:
        return cls(data["value"], to_bool(data["enabled"]))

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "enabled": self.enabled}
