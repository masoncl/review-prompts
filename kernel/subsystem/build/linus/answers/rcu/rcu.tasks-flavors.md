| Flavour | Reader | Update side outside `kernel/rcu/` | In-tree users, for example |
|---|---|---|---|
| Tasks RCU, `CONFIG_TASKS_RCU` | unmarked | `call_rcu_tasks()`, `synchronize_rcu_tasks()`, `rcu_barrier_tasks()` | `kernel/kprobes.c`, `kernel/bpf/trampoline.c` |
| Tasks Rude RCU, `CONFIG_TASKS_RUDE_RCU` | unmarked; any preemption-disabled region on an online CPU, idle CPUs included | `synchronize_rcu_tasks_rude()` only | `kernel/trace/ftrace.c` |
| Tasks Trace RCU, `CONFIG_TASKS_TRACE_RCU` | marked; may sleep | `call_rcu_tasks_trace()`, `synchronize_rcu_tasks_trace()`, `rcu_barrier_tasks_trace()`, `rcu_tasks_trace_expedite_current()` | sleepable BPF, faultable tracepoints, uprobes |

- `call_rcu_tasks_rude()`: `static` in `kernel/rcu/tasks.h`, used only to
  build `synchronize_rcu_tasks_rude()`; there is no rcu_barrier_tasks_rude().
- `synchronize_rcu_tasks_rude()`: returns at once, waiting for nothing, when
  `CONFIG_ARCH_WANTS_NO_INSTR` is set and `CONFIG_FORCE_TASKS_RUDE_RCU` is
  not.
- `CONFIG_TASKS_RCU`: `default NEED_TASKS_RCU && PREEMPTION` in
  `kernel/rcu/Kconfig`; users select `NEED_TASKS_RCU`, so a kernel without
  `PREEMPTION` has Tasks RCU configured out unless `FORCE_TASKS_RCU` is set.
- `CONFIG_TASKS_RCU` off: `call_rcu_tasks` and `synchronize_rcu_tasks` are
  macros for `call_rcu` and `synchronize_rcu` in `include/linux/rcupdate.h`.
- `rcu_barrier_tasks()` with `CONFIG_TASKS_RCU` off: declared, never defined,
  no macro fallback; a caller fails at link time.
- `CONFIG_TASKS_RUDE_RCU` off: `synchronize_rcu_tasks_rude()` has neither
  declaration nor fallback.
- `CONFIG_TASKS_TRACE_RCU` off: `rcu_read_lock_trace()`,
  `rcu_read_unlock_trace()` and `call_rcu_tasks_trace()` are inlines that
  `BUG()`; they are not no-ops and do not fall back to RCU.
- `guard(rcu_tasks_trace)` with `CONFIG_TASKS_TRACE_RCU` off: still defined,
  built from the two `BUG()` stubs.
- `CONFIG_TASKS_TRACE_RCU` off: `synchronize_rcu_tasks_trace()`,
  `rcu_barrier_tasks_trace()`, `rcu_tasks_trace_expedite_current()`,
  `rcu_read_lock_tasks_trace()` and `rcu_read_unlock_tasks_trace()` have no
  definition at all, so a caller does not compile.
