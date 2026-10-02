- `__scoped_guard()` loop exit: the condition is evaluated once, before the
  body; the loop ends because the increment clause `({ goto _label; })` jumps
  to a `break`, not because the condition turns false.
- `scoped_class()` in `include/linux/cleanup.h`: same `for` / `if (0)` /
  `else` shape with an empty condition, so `break` and `continue` behave the
  same in it and in its wrappers, for example `scoped_with_creds()` in
  `include/linux/cred.h`.
- `break` inside `scoped_guard()`: used in-tree on purpose as "leave the
  guard early", for example `try_to_wake_up()` in `kernel/sched/core.c`.
- **Potentially unsafe usage**: `break` or `continue` in a `scoped_guard()`
  body that sits inside a loop.
  - Unsafe: when the `break` or `continue` binds to the `scoped_guard()`
    itself, not to a loop or `switch` nested in its body, and a statement
    between the end of the `scoped_guard()` body and the end of the enclosing
    loop body must not run for that case; it runs, without the lock.
  - Safe: `break` to leave only the guard, with a flag tested right after it,
    as `get_modules_for_addrs()` in `kernel/trace/bpf_trace.c` does with
    `skip_add` followed by `if (skip_add) continue;`.
  - Safe: `continue` when the only statement after the `scoped_guard()` in the
    loop body is one that may run anyway, as in `vmstat_shepherd()` in
    `mm/vmstat.c`, where only `cond_resched()` follows.
