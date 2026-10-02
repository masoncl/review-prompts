- What reports a reader that sleeps, and what each check needs:

| Check | Needs | Reports |
|---|---|---|
| `rcu_note_context_switch()` in `kernel/rcu/tree_plugin.h` | `CONFIG_PREEMPT_RCU` only | `WARN_ONCE()` "Voluntary context switch within RCU read-side critical section!" |
| `rcu_preempt_sleep_check()` via `rcu_sleep_check()` | `CONFIG_PROVE_RCU` and `CONFIG_PREEMPT_RCU=n` | "Illegal context switch in RCU read-side critical section" |
| `__might_resched()` | `CONFIG_DEBUG_ATOMIC_SLEEP` | "sleeping function called from invalid context", in both builds |
| `schedule_debug()` | `CONFIG_PREEMPT_COUNT` and `CONFIG_PREEMPT_RCU=n` | "scheduling while atomic", no debug option needed |
| `check_wait_context()` in `kernel/locking/lockdep.c` | `CONFIG_PROVE_LOCKING` | "[ BUG: Invalid wait context ]" |

- `rcu_preempt_sleep_check()`: is empty under `CONFIG_PREEMPT_RCU`, so
  `rcu_sleep_check()` never reports on `rcu_lock_map` there.
- `rcu_sleep_check()`: is defined under `CONFIG_PROVE_RCU`, not
  `CONFIG_DEBUG_ATOMIC_SLEEP`. `schedule_debug()` calls it too, so with
  `CONFIG_PROVE_RCU` alone it still runs at every `__schedule()`.
- `__might_resched()` under `CONFIG_PREEMPT_RCU`: `resched_offsets_ok()` adds
  `rcu_preempt_depth()` to the count it compares, so `might_sleep()` inside
  `rcu_read_lock()` is reported although `preempt_count()` is 0.
- `check_wait_context()`: `rcu_lock_map` has
  `wait_type_inner = LD_WAIT_CONFIG`, so acquiring a `LD_WAIT_SLEEP` lock
  such as a mutex inside `rcu_read_lock()` is reported at the acquisition, in
  every RCU build, whether or not the lock is contended; a trylock is not
  checked.
- `CONFIG_PREEMPT_RT`, blocking on `spinlock_t` or `rwlock_t`:
  `schedule_rtlock()` passes `SM_RTLOCK_WAIT`, which `__schedule()` treats as
  a preemption, so `rcu_note_context_switch()` does not warn.
- `rtlock_might_resched()` in `kernel/locking/spinlock_rt.c`: passes the
  current `rcu_preempt_depth()` as the expected depth, so RCU nesting never
  fails it; a nonzero `preempt_count()` or disabled interrupts do.
