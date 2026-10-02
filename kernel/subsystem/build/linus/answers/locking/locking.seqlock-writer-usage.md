| Form | Assert | Lockdep acquire | `preempt_disable()` if `seqprop_preemptible()` |
|---|---|---|---|
| `write_seqcount_begin()`, `write_seqcount_begin_nested()` | yes | yes | yes |
| `raw_write_seqcount_begin()` | no | no | yes |
| `do_write_seqcount_begin()`, used by `write_seqlock()` | no | yes | no |
| `do_raw_write_seqcount_begin()` | no | no | no |
| `write_seqcount_invalidate()` | no | no | no |
| `raw_write_seqcount_barrier()` | no | no | no |

- `seqcount_mutex_t` write section on non-PREEMPT_RT: runs with preemption
  disabled by `write_seqcount_begin()`, so it must not sleep although the
  mutex is held.
- **Potentially unsafe usage**: a write section that can be preempted.
  - Unsafe: when any reader spins until the count is even, as
    `read_seqcount_begin()`, `raw_read_seqcount_begin()` and `read_seqbegin()`
    do outside the PREEMPT_RT case below; `__read_seqcount_begin()` spins
    while the count is odd.
  - Safe: when every reader uses a form that does not wait.
    `copy_page_range()` in `mm/memory.c` writes `write_protect_seq` with
    `raw_write_seqcount_begin()`; its reader `gup_fast()` uses
    `raw_seqcount_try_begin()`.
  - Safe: `ri_timer()` in `kernel/events/uprobes.c`, whose reader
    `free_ret_instance()` uses `raw_seqcount_try_begin()`, which does not
    wait.
  - Safe: on PREEMPT_RT, when the counter is a `seqcount_spinlock_t`,
    `seqcount_rwlock_t`, `seqcount_mutex_t` or `seqlock_t` and the writer
    holds the associated lock, as `write_seqlock()` does; on an odd count
    `seqprop_sequence()` locks and unlocks that lock, so the reader blocks
    until the writer is done.
- The raw form is what lets `copy_page_range()` and `ri_timer()` pass:
  `write_seqcount_begin()` on a `seqcount_t` would trip
  `lockdep_assert_preemption_disabled()`, for `ri_timer()` on PREEMPT_RT
  only.
- `write_seqcount_invalidate()`: `smp_wmb()`, then adds 2; the count stays
  even, so no reader waits and every section already open fails its retry.
- `write_seqcount_invalidate()` is used repeatedly on live objects:
  `__d_drop()` in `fs/dcache.c` on unhash, and
  `intel_gt_invalidate_tlb_full()` in `drivers/gpu/drm/i915/gt/intel_tlb.c`.
- `raw_write_seqcount_barrier()` users: `__run_hrtimer()` in
  `kernel/time/hrtimer.c` and `unix_peek_fpl()` in `net/unix/garbage.c`; not
  the dcache and not `mm_lock_seq`, which uses
  `do_raw_write_seqcount_begin()`.
- **Unsafe usage**: calling `write_seqcount_invalidate()` or
  `raw_write_seqcount_barrier()` from two writers at once; both do plain
  non-atomic increments and check nothing.
  - Safe: under the lock that serializes the counter's writers;
    `unix_peek_fpl()` takes a spinlock only for that, `__run_hrtimer()` holds
    `cpu_base->lock`.
