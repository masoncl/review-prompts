All in `include/linux/rcupdate.h` except the SRCU
form. `rcu_dereference()`, `rcu_dereference_bh()`, `rcu_dereference_sched()`,
`rcu_dereference_all()` and `srcu_dereference()` pass `c` = 0.

| Primitive | Load | Lockdep passes when `c` or | `rcu_check_sparse()` |
|---|---|---|---|
| `rcu_dereference_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_held()`: `rcu_lock_map` held, so `rcu_read_lock()` only | yes |
| `rcu_dereference_bh_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_bh_held()`: `in_softirq() \|\| irqs_disabled()` | yes |
| `rcu_dereference_sched_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_sched_held()`: `rcu_sched_lock_map` held or `!preemptible()` | yes |
| `rcu_dereference_all_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_any_held()`: any of the three maps held or `!preemptible()` | yes |
| `srcu_dereference_check(p, ssp, c)` | `READ_ONCE()` | `srcu_read_lock_held(ssp)` | yes |
| `rcu_dereference_raw_check(p)` | `READ_ONCE()` | always: the condition is the constant 1 | yes |
| `rcu_dereference_raw(p)` | `READ_ONCE()` | always: no `RCU_LOCKDEP_WARN()` | no |
| `rcu_access_pointer(p)` | `READ_ONCE()` | always: no `RCU_LOCKDEP_WARN()` | yes |
| `rcu_dereference_protected(p, c)` | plain | `c` alone | yes |

- `rcu_dereference()` in a preempt-disabled region or under
  `rcu_read_lock_sched()` alone, or without `CONFIG_PREEMPT_RT` in a
  BH-disabled region or under `rcu_read_lock_bh()` alone: lockdep splat, since
  those do not acquire `rcu_lock_map`. Use `rcu_dereference_all()`,
  `rcu_dereference_bh()` or `rcu_dereference_sched()`.
- `rcu_read_lock_held_common()` in `kernel/rcu/update.c`: runs first in the
  four RCU `_held()` helpers; with lockdep enabled and `!rcu_is_watching()` or
  `!rcu_lockdep_current_cpu_online()` they return false even inside
  `rcu_read_lock()`. `srcu_read_lock_held()` does not call it.
- rcu_dereference_raw_notrace() and rcu_dereference_index_check(): not defined
  here. `rcu_dereference_raw_check()` and `srcu_dereference_notrace()` pass the
  constant 1 as the condition, so they never call a `_held()` helper.
- `rcu_dereference_raw()` with a concurrent writer: the load is `READ_ONCE()`,
  it cannot tear. Only `rcu_dereference_protected()` needs writers excluded.
- `list_for_each_entry_rcu()`: loads through `list_entry_rcu()`, a bare
  `READ_ONCE()`. `hlist_for_each_entry_rcu()` uses `rcu_dereference_raw()`.
- `__list_check_rcu()` in `include/linux/rculist.h`: the only check that
  `list_for_each_entry_rcu()` and `hlist_for_each_entry_rcu()` make; compiled
  in only under `CONFIG_PROVE_RCU_LIST`; passes on `cond` or
  `rcu_read_lock_any_held()`.
- `__rcu_guarded`: `__rcu` plus `__guarded_by(RCU)`, checked at compile time
  under `CONFIG_WARN_CONTEXT_ANALYSIS`, and only for objects whose Makefile
  sets `CONTEXT_ANALYSIS := y` or the per-object form, as
  `CONTEXT_ANALYSIS_kcov.o := y` in `kernel/Makefile`, unless
  `CONFIG_WARN_CONTEXT_ANALYSIS_ALL` is set.
  `rcu_access_pointer()`, `rcu_assign_pointer()`, `RCU_INIT_POINTER()` and
  `unrcu_pointer()` are wrapped in `context_unsafe()`;
  `__rcu_dereference_check()` and `__rcu_dereference_protected()` are not.
- `srcu_dereference_check()`: calls `__srcu_read_lock_must_hold()`, declared
  `__must_hold_shared(ssp)`, whatever `c` is.
