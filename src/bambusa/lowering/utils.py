"""Utilities shared by lowering routines."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Optional

from ..ir import Mask, SSAValue


class SSANamer:
    """Generate unique SSA value names with stable human-readable prefixes."""

    def __init__(self, prefix: str = "%") -> None:
        self._prefix = prefix
        self._counters = defaultdict(int)

    def fresh(self, hint: str) -> str:
        idx = self._counters[hint]
        self._counters[hint] += 1
        return f"{self._prefix}{hint}{idx}"

    def value(self, hint: str) -> SSAValue:
        return SSAValue(self.fresh(hint))

    def mask(self, hint: str) -> Mask:
        return Mask(self.fresh(hint))


def compose_masks(
    builder: "MaskBuilderProtocol",
    *masks: Optional[Mask],
    hint: str = "mask",
) -> Mask:
    """Combine masks using logical AND semantics."""

    filtered = [m for m in masks if m is not None]
    if not filtered:
        return builder.true_mask

    result = filtered[0]
    for other in filtered[1:]:
        if other is result:
            continue
        result = builder.mask_and(result, other, hint=hint)
    return result


class MaskBuilderProtocol:
    """Protocol for builders that support mask composition."""

    true_mask: Mask

    def mask_and(self, left: Mask, right: Mask, *, hint: str) -> Mask:  # pragma: no cover - protocol
        raise NotImplementedError


__all__ = ["SSANamer", "compose_masks", "MaskBuilderProtocol"]

