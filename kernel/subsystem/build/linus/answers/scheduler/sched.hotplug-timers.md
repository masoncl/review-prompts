- `rq->fair_server`: stopped by `dl_server_stop()` called directly from
  `sched_cpu_dying()` under the rq lock, after `update_rq_clock()`.
- `rq->ext_server`: exists under `CONFIG_SCHED_CLASS_EXT`; stopped in
  `sched_cpu_dying()` right after `rq->fair_server`.
- `rq_offline_fair()`: does not call `dl_server_stop()`; no `->rq_offline`
  hook stops a deadline server.
- `sched_cpu_dying()` ordering: runs after `hrtimers_cpu_dying()` and after
  `__cpu_disable()`, so the CPU's queued hrtimers are already on another
  CPU's base and `cpu_online()` is false when the servers are stopped.
- `dl_server_start()` offline guard: `WARN_ON_ONCE(!cpu_online(cpu_of(rq)))`
  followed by return, placed after the `update_curr` call and before
  `dl_server_active` is set.
- `dl_server_start()`: does not test `rq->online` or `cpu_active()`; its other
  early returns are on `!dl_server()`, `dl_server_active`, `!dl_runtime` and
  `!dl_bw_attached`.
- Between `sched_cpu_deactivate()` and `__cpu_disable()`: the CPU is inactive
  with `rq->online` 0 but still `cpu_online()`, so `dl_server_start()` still
  starts a server there.
- `hrtick_enabled()` in `kernel/sched/sched.h`: tests `cpu_active()`; this is
  what stops hrtick arming after `sched_cpu_deactivate()`; `hrtick_start()`
  has no test of its own.
- `hrtick_clear()` in `sched_cpu_dying()`: called after the rq lock is
  dropped.
- hrtimer started on the dying CPU after `hrtimers_cpu_dying()`:
  `get_target_base()` in `kernel/time/hrtimer.c` selects the base of an
  online housekeeping CPU, even with `HRTIMER_MODE_PINNED`; it does not sit
  on the offline base.
- `dl_se->dl_timer`: not pinned; `start_dl_timer()` uses
  `HRTIMER_MODE_ABS_HARD`; `rq->hrtick_timer` is started with
  `HRTIMER_MODE_ABS_PINNED_HARD`.
- `sched_tick_stop()`: does not cancel the delayed work; under
  `CONFIG_NO_HZ_FULL`, for a CPU that is not a `HK_TYPE_KERNEL_NOISE`
  housekeeping CPU, it sets `TICK_SCHED_REMOTE_OFFLINING` and the next
  `sched_tick_remote()` run moves to `TICK_SCHED_REMOTE_OFFLINE` without
  requeueing.
- Cancelling the remote tick work in `sched_tick_stop()`: would leave
  `TICK_SCHED_REMOTE_OFFLINING`, and `sched_tick_start()` queues the work only
  from `TICK_SCHED_REMOTE_OFFLINE`.
- `rq->scx.rescue.timer` (`CONFIG_EXT_SUB_SCHED`, `kernel/sched/ext/sub.c`):
  a per-rq `TIMER_PINNED` timer; stopped in `sched_cpu_deactivate()` through
  `rq_offline_scx()` and `scx_rescue_flush()`, which calls `timer_delete()`.
- `scx_rescue_timer_arm()`: reached for new work only from
  `scx_resolve_local_dsq()`, after its `scx_rq_online()` test; the timer
  function rearms only while a rescuee exists, and `scx_rescue_flush()`
  empties both.
- `set_rq_offline()`: also called from `rq_attach_root()` in
  `kernel/sched/topology.c` for a CPU that stays up, so a `->rq_offline` hook
  is not a hotplug-only event; `scx_rescue_flush()` returns early when
  `cpu_active()`.
- Per-task `dl_se->dl_timer`: no scheduler hotplug callback stops it;
  `dl_task_timer()` calls `dl_task_offline_migration()` when `rq->online`
  is 0.
- **Unsafe usage**: calling `hrtick_start()` without a preceding
  `hrtick_enabled_fair()` or `hrtick_enabled_dl()` test; `hrtick_clear()` in
  `sched_cpu_dying()` is the last hotplug cancel of the timer, and `hrtick()`
  warns when it runs on a CPU other than `cpu_of(rq)`.
  - Safe: test first under the rq lock, as `hrtick_update()` in
    `kernel/sched/fair.c` does; `hrtick_enabled()` defines the gate.
- **Potentially unsafe usage**: calling `dl_server_start()` for an rq the
  caller did not get from task placement.
  - Unsafe: when the CPU comes from a loop over possible CPUs or from user
    input and `cpu_online()` was not tested; `dl_server_start()` warns and
    returns.
  - Safe: test `cpu_online()` under the rq lock first, as
    `dl_server_attach_bw()` and `dl_server_swap_bw()` do, or return `-EBUSY`
    as `sched_server_write_common()` in `kernel/sched/debug.c` does.
- **Potentially unsafe usage**: `hrtimer_cancel()` on an rq timer while
  holding the rq lock.
  - Unsafe: when the callback can be running on another CPU, as with the
    unpinned `dl_se->dl_timer`; `dl_server_timer()` takes the rq lock.
  - Safe: `hrtimer_try_to_cancel()` as `dl_server_stop()` does; it clears
    `dl_throttled`, and `dl_server_timer()` returns `HRTIMER_NORESTART` when
    `dl_throttled` is 0 under the rq lock.
  - Safe: `hrtick_schedule_exit()`, where `rq->hrtick_timer` is pinned to the
    local CPU and IRQs are off, so `hrtick()` cannot be running.
