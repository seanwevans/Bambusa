"""Utilities for replaying and inspecting Bambusa execution timelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional
import json


@dataclass(frozen=True)
class TimelineEntry:
    """Represents a snapshot loaded from a structured execution log."""

    step: int
    instruction: Mapping[str, Any]
    state: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TimelineEntry":
        return cls(
            step=payload["step"],
            instruction=payload.get("instruction", {}),
            state=payload.get("state", {}),
        )


class Timeline:
    """Navigates execution histories produced by :class:`Executor`."""

    def __init__(self, entries: Iterable[TimelineEntry]):
        self._entries: List[TimelineEntry] = list(entries)
        if not self._entries:
            raise ValueError("Timeline requires at least one entry")
        self._index: int = 0

    # ------------------------------------------------------------------
    # Construction helpers

    @classmethod
    def from_log(cls, path: str | Path) -> "Timeline":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_stream(handle)

    @classmethod
    def from_stream(cls, stream: Iterable[str]) -> "Timeline":
        entries: List[TimelineEntry] = []
        for line in stream:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            entries.append(TimelineEntry.from_payload(payload))
        if not entries:
            raise ValueError("Log stream produced no entries")
        return cls(entries)

    # ------------------------------------------------------------------
    # Navigation

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def current_step(self) -> int:
        return self._entries[self._index].step

    @property
    def current_instruction(self) -> Mapping[str, Any]:
        return self._entries[self._index].instruction

    @property
    def current_state(self) -> Mapping[str, Any]:
        return self._entries[self._index].state

    def seek(self, step: int) -> TimelineEntry:
        for idx, entry in enumerate(self._entries):
            if entry.step == step:
                self._index = idx
                return entry
        raise IndexError(f"No snapshot recorded for step {step}")

    def next(self) -> TimelineEntry:
        if self._index >= len(self._entries) - 1:
            raise IndexError("Already at the end of the timeline")
        self._index += 1
        return self._entries[self._index]

    def prev(self) -> TimelineEntry:
        if self._index <= 0:
            raise IndexError("Already at the beginning of the timeline")
        self._index -= 1
        return self._entries[self._index]

    def iter_from(self, step: Optional[int] = None) -> Iterator[TimelineEntry]:
        if step is not None:
            self.seek(step)
        for entry in self._entries[self._index :]:
            yield entry

    # ------------------------------------------------------------------
    # Forking and diffing

    def fork(self, *, at_step: Optional[int] = None) -> "Timeline":
        clone = Timeline(self._entries)
        if at_step is None:
            clone._index = self._index
        else:
            clone.seek(at_step)
        return clone

    def diff(
        self,
        other: "Timeline",
        *,
        step: Optional[int] = None,
        other_step: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Return a diff between two timelines.

        Parameters
        ----------
        other:
            The timeline to compare against.
        step:
            The step number for ``self``.  Defaults to the current step.
        other_step:
            Step number on ``other``.  When omitted the other's current step is
            used.  When provided alongside ``step`` this allows diffing
            different positions in the execution history (useful for comparing
            forks that have advanced independently).
        """

        left_state = self._state_at(step)
        comparison_step = other_step if other_step is not None else (step if step is not None else other.current_step)
        right_state = other._state_at(comparison_step)
        return _diff_states(left_state, right_state)

    def _state_at(self, step: Optional[int]) -> Mapping[str, Any]:
        if step is None:
            return self.current_state
        for entry in self._entries:
            if entry.step == step:
                return entry.state
        raise IndexError(f"No snapshot for step {step}")

    def to_json(self) -> List[Dict[str, Any]]:
        return [
            {
                "step": entry.step,
                "instruction": entry.instruction,
                "state": entry.state,
            }
            for entry in self._entries
        ]


def _diff_states(left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Compute a structural diff between two mapping-like states."""

    removed = {}
    added = {}
    changed = {}
    left_keys = set(left.keys())
    right_keys = set(right.keys())

    for key in left_keys - right_keys:
        removed[key] = left[key]
    for key in right_keys - left_keys:
        added[key] = right[key]
    for key in left_keys & right_keys:
        if left[key] != right[key]:
            changed[key] = {"left": left[key], "right": right[key]}

    return {"added": added, "removed": removed, "changed": changed}


__all__ = ["Timeline", "TimelineEntry"]
