- `data_race()` cases in
  `tools/memory-model/Documentation/access-marking.txt`, all four:
  - diagnostic reads;
  - reads whose value is checked against a later marked load, such as the
    seed of a `cmpxchg()` loop;
  - reads that feed error-tolerant heuristics;
  - writes that set values feeding error-tolerant heuristics.
- Lock-protected writes whose only lockless readers are diagnostic: the
  writes stay plain and the read uses `data_race()`; `WRITE_ONCE()` on the
  writer is for lockless readers that the algorithm depends on.
- `data_race(READ_ONCE(x))`: not redundant; `READ_ONCE()` restricts the
  compiler, `data_race()` stops KCSAN reporting the read against plain
  lock-protected writes.
- Asking to replace `data_race()` by `READ_ONCE()` on a diagnostic read is
  wrong when the writers are plain under a lock: KCSAN then reports the read
  wherever the plain write is not assumed atomic (see the last bullet), and
  marking the writers to quiet it hides buggy lockless accesses.
- `data_race()` on a heuristic read: only where something else, such as
  `barrier()` or a lock acquisition, forces a reload; if any possible bogus
  value could break the heuristic, use `READ_ONCE()`.
- `__data_racy`: `volatile` under `CONFIG_KCSAN`, empty otherwise
  (`include/linux/compiler_types.h`); in a non-KCSAN build it gives no
  protection against tearing or fusing.
- `ASSERT_EXCLUSIVE_WRITER()`: does not replace a marking; with lockless
  readers the write stays `WRITE_ONCE()` and the assertion sits beside it, to
  catch a second writer even if that writer is marked.
- `ASSERT_EXCLUSIVE_ACCESS()`: goes with plain accesses, such as
  single-threaded initialisation or after the last reference is dropped; it
  reports a concurrent access even if that access is marked.
- Plain writes and KCSAN in a default build: `is_atomic()` in
  `kernel/kcsan/core.c` treats aligned, non-compound plain writes up to word
  size as atomic under `CONFIG_KCSAN_ASSUME_PLAIN_WRITES_ATOMIC` (default y
  unless `CONFIG_KCSAN_STRICT`), so a race of such a write with another such
  write or with a marked read is not reported; an assertion is never treated
  as atomic and still catches it.
