- `readsX()`, `writesX()`: keep the guarantees of `readX_relaxed()` and
  `writeX_relaxed()`, so on a mapping with default I/O attributes accesses
  from one CPU thread to one peripheral stay in program order; they are not
  unordered. See "KERNEL I/O BARRIER EFFECTS" in
  `Documentation/memory-barriers.txt`.
- `insX()`, `outsX()`: same guarantees as `readsX()` and `writesX()`, so
  weaker than `inX()` and `outX()`, which match `readX()` and `writeX()`.
