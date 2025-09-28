"""Persistent heap structures and mask-friendly primitives.

This module implements a minimal persistent heap that stores immutable vector
objects. Each update produces a new *version* of the vector while keeping all
previous versions available. The implementation is intentionally simple but
carefully avoids mutating previously produced tuples so that property-based
tests can reason about history preservation.

The API mirrors the expectations of the branchless Bambusa runtime. Operations
accept explicit masks so callers never need to branch: the mask determines
which elements are observed or updated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Sequence, Tuple, Union

Mask = Union[bool, Sequence[bool]]
Indices = Union[int, Sequence[int]]
Values = Union[Any, Sequence[Any]]


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _ensure_tuple(value: Union[Any, Sequence[Any]]) -> Tuple[Any, ...]:
    if _is_sequence(value):
        return tuple(value)
    return (value,)


def _broadcast_mask(mask: Mask, length: int) -> Tuple[bool, ...]:
    mask_tuple = _ensure_tuple(mask)
    if len(mask_tuple) == 1 and length != 1:
        mask_tuple = mask_tuple * length
    if len(mask_tuple) != length:
        raise ValueError(f"Mask of length {len(mask_tuple)} cannot broadcast to {length}")
    return tuple(bool(m) for m in mask_tuple)


def _normalise_index(index: int, length: int) -> int:
    if index < 0:
        index += length
    if index < 0 or index >= length:
        raise IndexError(f"Index {index} out of range for vector of length {length}")
    return index


@dataclass(frozen=True)
class PersistentVector:
    """A lightweight handle to a specific version of a heap-backed vector."""

    heap: "PersistentHeap"
    handle: int
    version: int

    def materialise(self) -> Tuple[Any, ...]:
        """Return the immutable contents of the vector."""
        return self.heap.get_version_data(self.handle, self.version)

    # Alias for users that prefer American spelling.
    materialize = materialise

    def __iter__(self):
        return iter(self.materialise())

    def __len__(self) -> int:
        return len(self.materialise())

    def __getitem__(self, index: int) -> Any:
        data = self.materialise()
        return data[_normalise_index(index, len(data))]

    def __repr__(self) -> str:
        data = self.materialise()
        return f"PersistentVector(handle={self.handle}, version={self.version}, data={data!r})"


class PersistentHeap:
    """A persistent heap that stores immutable vector versions."""

    def __init__(self) -> None:
        self._next_handle = 0
        self._versions: List[List[Tuple[Any, ...]]] = []

    # ------------------------------------------------------------------
    # Allocation & version management
    # ------------------------------------------------------------------
    def allocate(
        self,
        values: Union[int, Iterable[Any]],
        *,
        mask: Mask | None = None,
        fill_value: Any = 0,
    ) -> PersistentVector:
        """Allocate a new persistent vector.

        Args:
            values: Either an integer specifying the length of the vector to
                allocate, or an iterable containing the initial values.
            mask: Optional mask. When provided, masked-out slots will be filled
                with ``fill_value``.
            fill_value: Value used for masked-out slots and for allocations
                created from a length integer.
        """

        if isinstance(values, int):
            if values < 0:
                raise ValueError("Vector length must be non-negative")
            data = tuple(fill_value for _ in range(values))
        else:
            data_list = list(values)
            if mask is not None:
                mask_tuple = _broadcast_mask(mask, len(data_list))
                data_list = [
                    original if active else fill_value
                    for original, active in zip(data_list, mask_tuple)
                ]
            data = tuple(data_list)

        handle = self._next_handle
        self._next_handle += 1
        self._versions.append([data])
        return PersistentVector(self, handle, 0)

    def get_version_data(self, handle: int, version: int) -> Tuple[Any, ...]:
        try:
            return self._versions[handle][version]
        except IndexError as exc:  # pragma: no cover - defensive programming
            raise IndexError("Invalid handle/version pair") from exc

    def _commit(self, handle: int, data: Sequence[Any]) -> PersistentVector:
        data_tuple = tuple(data)
        self._versions[handle].append(data_tuple)
        return PersistentVector(self, handle, len(self._versions[handle]) - 1)

    # ------------------------------------------------------------------
    # Mask-friendly operations
    # ------------------------------------------------------------------
    def masked_load(
        self,
        vector: PersistentVector,
        indices: Indices,
        mask: Mask,
        default: Any | None = None,
    ) -> Tuple[Any, ...]:
        data = vector.materialise()
        idx_tuple = tuple(int(i) for i in _ensure_tuple(indices))
        mask_tuple = _broadcast_mask(mask, len(idx_tuple))
        result = []
        for idx, active in zip(idx_tuple, mask_tuple):
            normalised = _normalise_index(idx, len(data))
            result.append(data[normalised] if active else default)
        return tuple(result)

    def masked_store(
        self,
        vector: PersistentVector,
        indices: Indices,
        values: Values,
        mask: Mask,
    ) -> PersistentVector:
        data = list(vector.materialise())
        idx_tuple = tuple(int(i) for i in _ensure_tuple(indices))
        value_tuple = _ensure_tuple(values)
        if len(idx_tuple) != len(value_tuple):
            raise ValueError("Indices and values must be the same length")
        mask_tuple = _broadcast_mask(mask, len(idx_tuple))
        for idx, value, active in zip(idx_tuple, value_tuple, mask_tuple):
            if not active:
                continue
            normalised = _normalise_index(idx, len(data))
            data[normalised] = value
        return self._commit(vector.handle, data)

    def compact(self, vector: PersistentVector, mask: Mask) -> PersistentVector:
        data = vector.materialise()
        mask_tuple = _broadcast_mask(mask, len(data))
        compacted = [value for value, active in zip(data, mask_tuple) if active]
        return self._commit(vector.handle, compacted)


# ----------------------------------------------------------------------
# Convenience wrappers exposed as primitives
# ----------------------------------------------------------------------
def masked_load(
    vector: PersistentVector,
    indices: Indices,
    mask: Mask,
    default: Any | None = None,
) -> Tuple[Any, ...]:
    """Load elements from a vector while respecting a mask."""

    return vector.heap.masked_load(vector, indices, mask, default)


def masked_store(
    vector: PersistentVector,
    indices: Indices,
    values: Values,
    mask: Mask,
) -> PersistentVector:
    """Store elements into a vector while respecting a mask."""

    return vector.heap.masked_store(vector, indices, values, mask)


def compact(vector: PersistentVector, mask: Mask) -> PersistentVector:
    """Compact a vector using the provided mask."""

    return vector.heap.compact(vector, mask)


__all__ = [
    "PersistentHeap",
    "PersistentVector",
    "masked_load",
    "masked_store",
    "compact",
]
