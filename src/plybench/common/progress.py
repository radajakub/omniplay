from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def track(items: Iterable[T], desc: str, total: int | None = None, enabled: bool | None = None) -> Iterator[T]:
    enabled = sys.stderr.isatty() if enabled is None else enabled
    if not enabled:
        yield from items
        return
    from tqdm import tqdm

    yield from tqdm(items, desc=desc, total=total, leave=False)
