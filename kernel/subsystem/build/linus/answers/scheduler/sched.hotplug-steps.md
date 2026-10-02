- `sched_cpu_deactivate()` context: runs in the cpuhp thread on the outgoing
  CPU, not in the control task; `CPUHP_AP_ACTIVE` is above
  `CPUHP_TEARDOWN_CPU`, so `_cpu_down()` hands it to `cpuhp_thread_fun()`.
- `sched_cpu_deactivate()` error return: only `dl_bw_deactivate()`, the first
  statement, before any state is changed.
- `cpuset_cpu_inactive()`: returns void; `sched_cpu_deactivate()` has no undo
  code and returns 0 after it.
- `sched_cpu_deactivate()` returning an error: the core does not call
  `sched_cpu_activate()`; `cpuhp_reset_state()` in `kernel/cpu.c` puts the
  state back at `CPUHP_AP_ACTIVE` and the rollback runs startup only for
  states above it.
- **Unsafe usage**: returning an error from `sched_cpu_deactivate()` after it
  has changed state; nothing restores `cpu_active()`, `rq->online` or
  `balance_push_callback`.
  - Safe: fail before the first change, as the `dl_bw_deactivate()` call does.
- Teardown failing below `CPUHP_AP_ACTIVE` down to `CPUHP_TEARDOWN_CPU`, for
  example `takedown_cpu()` when `__cpu_disable()` fails:
  `sched_cpu_activate()` runs and is the only undo for
  `sched_cpu_deactivate()`; `CPUHP_AP_SCHED_WAIT_EMPTY` has no startup.
- `sched_cpu_dying()` when `__cpu_disable()` fails: does not run;
  `take_cpu_down()` returns on the error before the DYING callbacks.
- `sched_cpu_dying()` return value: ignored; `take_cpu_down()` runs it
  through `cpuhp_invoke_callback_range_nofail()`, which only prints a warning
  on error.
- `sched_set_rq_offline()` and `nohz_balance_exit_idle()`: called from
  `sched_cpu_deactivate()`; `sched_cpu_dying()` does not touch `rq->online`.
- `sched_cpu_deactivate()` after `synchronize_rcu()`: calls
  `sched_domains_free_llc_id()`, which takes `sched_domains_mutex`, before
  `sched_set_rq_offline()`; `sched_cpu_activate()` has no direct counterpart.
- `sched_cpu_wait_empty()`: calls only `balance_hotplug_wait()` and then
  `sched_force_init_mm()`; it migrates nothing itself and there is no
  sched_force_ipi in this tree.
- `balance_hotplug_wait()` condition: `rq->nr_running == 1 &&
  !rq_has_pinned_tasks(rq)`.
- `sched_force_init_mm()`: `finish_cpu()` in `kernel/cpu.c` relies on it and
  warns if the idle task's `active_mm` is not `init_mm`.
- `balance_push_set(cpu, false)`: among the hotplug callbacks only
  `sched_cpu_activate()` calls it; `sched_cpu_dying()` leaves
  `balance_push_callback` installed, although the comment in
  `sched_cpu_deactivate()` points at `sched_cpu_dying()`.
- Bring-up failing above `CPUHP_AP_SCHED_WAIT_EMPTY` and below
  `CPUHP_AP_ACTIVE`: `sched_cpu_wait_empty()` runs without
  `sched_cpu_deactivate()` having run.
- State seen in that bring-up rollback: `cpu_active()` is still false,
  `balance_push_callback` is still installed from the previous offline or
  from boot, and `cpuhp_reset_state()` has set `cpu_dying()`, so
  `balance_push()` acts.
