# 🌱 Bambusa

> **Bambusa: Imperative syntax, functional core, branchless by construction.**

Bambusa is an experimental programming language designed for a compute-abundant future.  
It looks like C, but under the hood it compiles into **purely functional, immutable, branchless IR**.  

Why? Because one day the user won’t know — or care — how many CPUs they have.  
Whether it’s **dozens** or **hundreds of trillions**, compute will be a fluid utility.  
The bottleneck won’t be performance. It will be **predictability, correctness, and ergonomics**.

---

## 🌍 Ethos

- **For Humans, Not Machines**  
  Programming languages exist to make computers easier to use.  
  Bambusa preserves imperative ergonomics (`if`, `for`, assignments) so programmers can think naturally.  

- **Branchless by Construction**  
  Branches are forbidden in the lowered code.  
  Every `if/else`, `switch`, and `for` becomes a composition of **mask operations** (`select`, `masked_load`, `masked_store`).  
  This guarantees constant-time execution, no warp divergence, and easier verification.  

- **Immutable Core**  
  Every value is immutable.  
  Updates are modeled as **persistent data structures**: new versions are created, old ones masked out.  
  Garbage collection is just **stream compaction** — branchless, data-parallel, predictable.  

- **Timeline of States**  
  Programs don’t “mutate.” They generate **histories**: replayable, forkable timelines of state.  
  Debugging is just scrolling through history.  
  Forking an entire universe of computation is natural.  

- **Designed for Fluid Compute**  
  When CPUs are elastic and RAM is effectively infinite, there is no reason to optimize for scarcity.  
  Instead, Bambusa optimizes for **clarity, determinism, and correctness at scale**.  

---

## 🌿 Concepts

### 1. **Imperative Surface → Functional Core**
Programmers write:
```bambusa
fn max(a: int, b: int) -> int {
  if a > b then a else b
}
```

Compiler lowers to branchless IR:
```llvm
%cmp = icmp sgt i32 %a, %b
%res = select i1 %cmp, i32 %a, i32 %b
ret i32 %res
```

No branches. Pure expressions. SSA by default.

---

### 2. **Loops as Masked Folds**
```bambusa
fn sumUntil(arr: int[], n: int, len: int) -> int {
  sum = 0
  for i in 0..len {
    if i < n then sum = sum + arr[i]
  }
  return sum
}
```

Lowered to:
```
for i=0..len-1:
  mask = (i < n)
  sum = sum + select(mask, arr[i], 0)
```

Every iteration executes, masked as needed.

---

### 3. **Memory as Masks**
- Heap = flat array.  
- Allocation = carve out a mask segment.  
- Free = drop the mask.  
- Garbage collection = branchless stream compaction.  

Safe by construction: no dangling pointers, no UB.  

---

### 4. **Immutable / Persistent Structures**
Updating an array:
```bambusa
fn update(arr: int[], i: int, v: int) -> int[] {
  new = alloc(length(arr))
  for j in 0..length(arr) {
    new[j] = if j == i then v else arr[j]
  }
  return new
}
```

This produces a new version, leaving the old intact.  
Structural sharing can optimize copies, but immutability is the default.

---

### 5. **The Future Compute Model**
- CPUs scale elastically: dozens → trillions.  
- RAM behaves like a massive, super-local cache.  
- Compute is *trivial*, but reasoning about programs is not.  
- Bambusa gives you determinism, auditability, and branchless predictability.  

---

## 🌀 Inspirations

- **Functional languages (Haskell, ML):** purity, immutability, persistent data.  
- **GPU & SIMD programming:** predication, masks, warp-uniform execution.  
- **Cryptography:** constant-time, branchless coding.  
- **Real-time control:** predictable, deterministic timing.  

---

## 🚧 Status

Bambusa is in its **conceptual and prototyping stage**:
- ✅ Core branchless IR defined
- ✅ ANTLR grammar written
- ✅ Toy Python simulator implemented
- ⏳ Next: LLVM IR backend, timeline debugger, persistent heap runtime

## 🧪 Runtime opcodes

The Python runtime executes a lightweight dictionary-based IR.  Opcodes mirror
the structures emitted by the lowering pipeline so that tests, tooling, and the
eventual compiler backend agree on semantics.  Arithmetic instructions retain
their verb-style names (``add``, ``sub``, ``mul``), while comparisons use the
``cmp_<mnemonic>`` form that corresponds to the Bambusa surface syntax:

| Surface operator | Opcode   |
| ---------------- | -------- |
| ``==``           | ``cmp_eq`` |
| ``!=``           | ``cmp_ne`` |
| ``<``            | ``cmp_lt`` |
| ``<=``           | ``cmp_le`` |
| ``>``            | ``cmp_gt`` |
| ``>=``           | ``cmp_ge`` |

The resulting boolean can be wired directly into other branchless primitives
such as ``select`` or mask-producing operations.

## 🧭 Timeline Debugger

The Python runtime can emit a JSONL log describing each IR step.  Run a program
with the instrumented executor and pass a file path to ``log_path``:

```python
from bambusa.runtime.executor import Executor

steps = [
    {"op": "assign", "target": "x", "value": 1},
    {"op": "add", "target": "x", "value": 2},
]

executor = Executor(steps)
executor.run(log_path="run.log")
```

Inspect the execution afterwards using the CLI:

```bash
$ bambusa timeline run.log
```

The CLI also accepts ``-`` to read the log from standard input, which makes it
easy to pipe data directly from other tools:

```bash
$ cat run.log | bambusa timeline - --json
```

Interactive commands:

```
next / prev    step through the log
goto <step>    jump to an absolute step
state          show the current instruction + state
fork [step]    fork the history to explore an alternate path
diff [step]    compare against the original execution
```

Use ``--json`` for non-interactive consumption:

```bash
$ bambusa timeline run.log --json > timeline.json
```
