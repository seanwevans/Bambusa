import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from bambusa.runtime.persistent_heap import (  # noqa: E402
    PersistentHeap,
    compact,
    masked_load,
    masked_store,
)


def _random_vector(rng: random.Random, length: int, low: int, high: int) -> list[int]:
    return [rng.randint(low, high) for _ in range(length)]


def _random_mask(rng: random.Random, length: int) -> list[bool]:
    return [bool(rng.getrandbits(1)) for _ in range(length)]


def _random_updates(rng: random.Random, length: int) -> list[dict[str, list[int]]]:
    operations = []
    for _ in range(rng.randint(1, 6)):
        operations.append(
            {
                "values": _random_vector(rng, length, -256, 256),
                "mask": _random_mask(rng, length),
            }
        )
    return operations


@pytest.mark.parametrize("seed", range(32))
def test_masked_store_creates_new_versions(seed: int) -> None:
    rng = random.Random(seed)
    length = rng.randint(1, 6)
    initial = _random_vector(rng, length, -128, 128)
    updates = _random_updates(rng, length)

    heap = PersistentHeap()
    vector = heap.allocate(initial)

    history = [vector.materialise()]
    vectors = [vector]

    for update in updates:
        indices = tuple(range(len(vector)))
        new_vector = masked_store(vector, indices, update["values"], update["mask"])

        expected = tuple(
            new if mask else old
            for old, new, mask in zip(vector.materialise(), update["values"], update["mask"])
        )

        assert new_vector.handle == vector.handle
        assert new_vector.version != vector.version
        assert new_vector.materialise() == expected
        assert vector.materialise() == history[-1]

        history.append(new_vector.materialise())
        vectors.append(new_vector)
        vector = new_vector

    for snapshot, vec in zip(history, vectors):
        assert vec.materialise() == snapshot


@pytest.mark.parametrize("seed", range(32, 64))
def test_compact_preserves_history(seed: int) -> None:
    rng = random.Random(seed)
    length = rng.randint(1, 6)
    initial = _random_vector(rng, length, -256, 256)
    mask = _random_mask(rng, length)

    heap = PersistentHeap()
    vector = heap.allocate(initial)
    before = vector.materialise()

    compacted = compact(vector, mask)
    expected = tuple(value for value, active in zip(before, mask) if active)

    assert compacted.handle == vector.handle
    assert compacted.version != vector.version
    assert compacted.materialise() == expected
    assert vector.materialise() == before


@pytest.mark.parametrize("seed", range(64, 96))
def test_masked_load_is_pure(seed: int) -> None:
    rng = random.Random(seed)
    length = rng.randint(1, 6)
    initial = _random_vector(rng, length, -256, 256)
    mask = _random_mask(rng, length)

    heap = PersistentHeap()
    vector = heap.allocate(initial)
    before = vector.materialise()

    indices = tuple(range(len(initial)))
    default = -999
    loaded = masked_load(vector, indices, mask, default)

    assert vector.materialise() == before
    assert len(loaded) == len(indices)
    for idx, result, active in zip(indices, loaded, mask):
        expected = initial[idx] if active else default
        assert result == expected
