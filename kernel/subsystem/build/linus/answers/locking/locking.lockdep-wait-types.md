- Wait types that are easy to get wrong (outer `LD_WAIT_INV` means "use
  inner"):

| Map | inner | outer |
|---|---|---|
| `rcu_lock_map` | `LD_WAIT_CONFIG` | `LD_WAIT_FREE` |
| `rcu_bh_lock_map` | `LD_WAIT_CONFIG` | `LD_WAIT_FREE` |
| `rcu_sched_lock_map` | `LD_WAIT_SPIN` | `LD_WAIT_FREE` |
| `local_lock_t` (lock type `LD_LOCK_PERCPU`) | `LD_WAIT_CONFIG` | `LD_WAIT_INV` |
| SRCU `dep_map` | `LD_WAIT_INV` | `LD_WAIT_INV` |
| `struct percpu_rw_semaphore` | `LD_WAIT_INV` | `LD_WAIT_INV` |

- SRCU and `struct percpu_rw_semaphore`: initialised without a wait type
  (plain `lockdep_init_map()`, or a static initialiser that sets only
  `.name`), so acquiring them is never wait-context checked and holding them
  never lowers the context.
- `struct semaphore` and bit spinlocks: no lockdep map of their own, so
  `check_wait_context()` never sees them.
- Hardirq context: `LD_WAIT_SPIN` only when neither `current->hardirq_threaded`
  nor `current->irq_config` is set; otherwise `LD_WAIT_CONFIG`
  (`task_wait_context()` in `kernel/locking/lockdep.c`).
- `hardirq_threaded`: set by `__handle_irq_event_percpu()` when
  `irq_settings_can_thread()` is true and the action has none of
  `IRQF_NO_THREAD`, `IRQF_PERCPU`, `IRQF_ONESHOT`.
- `irq_config`: set by `lockdep_hrtimer_enter()` for non-hard timers, by
  `lockdep_irq_work_enter()` without `IRQ_WORK_HARD_IRQ`, and by
  `lockdep_posixtimer_enter()` (`include/linux/irqflags.h`).
- Read acquisitions: checked like any other; `check_wait_context()` does not
  test `read`.
- `check == 0` acquisitions: still checked; the RCU maps are acquired with
  `check` 0 and go through `check_wait_context()`.
- Skipped besides inner `LD_WAIT_INV` and trylock: maps keyed
  `__lockdep_no_track__`, and an acquisition with a `nest_lock` whose class
  equals that of the top held lock, which `__lock_acquire()` folds into the
  held lock and returns before the check.
- Held trylocks: only the lock being acquired is exempt as a trylock; a lock
  that was taken by trylock and is still held lowers the context for later
  acquisitions in the same irq context.
