| Interface | Carried from lock to unlock | Defined in |
|---|---|---|
| `rcu_read_lock_trace()`, `rcu_read_unlock_trace()` | nothing | `include/linux/rcupdate_trace.h` |
| `rcu_read_lock_tasks_trace()`, `rcu_read_unlock_tasks_trace()` | the returned `struct srcu_ctr __percpu *` | `include/linux/rcupdate_trace.h` |
| `guard(rcu_tasks_trace)` | nothing; wraps the `rcu_read_lock_trace()` pair | `DEFINE_LOCK_GUARD_0()` at the end of `include/linux/rcupdate_trace.h` |

- Pointer-carrying pair: there is no guard for it.
- Returned pointer, Tree SRCU: names one of the two `srcu_ctrs[]` elements,
  not a CPU; the unlock increments on whatever CPU it runs on and
  `srcu_readers_unlock_idx()` sums over all CPUs, so a reader may migrate
  between lock and unlock.
- `rcu_read_unlock_tasks_trace()`: calls `srcu_lock_release()` on the calling
  task's lockdep state, so under `CONFIG_DEBUG_LOCK_ALLOC` the lock and the
  unlock still have to run in one task, although the pair uses neither
  `trc_reader_nesting` nor `trc_reader_scp`.
- **Unsafe usage**: closing a `rcu_read_lock_tasks_trace()` reader with
  `rcu_read_unlock_trace()`.
  - Unsafe: `rcu_read_unlock_trace()` computes `trc_reader_nesting - 1`; with
    the count at 0 it stores -1 and skips `__srcu_read_unlock_fast()`, so the
    SRCU lock count is never balanced and no later grace period ends.
  - Safe: keep the returned pointer in a local and pass it to
    `rcu_read_unlock_tasks_trace()`, as `__bpf_trace_run()` in
    `kernel/trace/bpf_trace.c` does; the unlock's `scp` parameter is what
    `__srcu_read_unlock_fast()` increments.
