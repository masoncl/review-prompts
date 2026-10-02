- Servers counted in `total_bw`: only those with `dl_bw_attached` set. After
  boot that is `fair_server` alone; `ext_server` joins when a BPF scheduler is
  enabled, and `fair_server` leaves while all tasks are switched to sched_ext.
- Default share: 50 ms / 1000 ms per attached server per active CPU. With the
  default 100% limit that leaves deadline tasks 95% of each CPU when one server
  is attached.
- `dl_server_init()` adds nothing to `total_bw`. Server bandwidth enters
  through `dl_server_apply_params()` (at init, or for an attached server),
  `dl_server_attach_bw()`, `dl_server_swap_bw()`, `__dl_server_attach_root()`
  and `dl_server_add_bw()`.
- Inactive CPU: `dl_server_add_bw()` and `__dl_server_attach_bw_locked()` skip
  `total_bw` when `cpu_active()` is false; detach skips the subtraction too.
- `dl_server_apply_params()` with `init` false on a detached server: runs the
  overflow test, stores the parameters and leaves `total_bw` unchanged.
- Blocked deadline task: stays in `total_bw`; blocking only changes
  `running_bw`.
- Task that left the class while queued, or is `TASK_DEAD`: stays in
  `total_bw` until its 0-lag time. `task_non_contending()` subtracts at once
  if that time has passed, otherwise `inactive_task_timer()` does.
- cpuset migration in flight: `cpuset_reserve_dl_bw()` adds the bandwidth of
  the moving tasks that change root domain (`dl_task_needs_bw_move()`) to the
  destination root domain with `dl_bw_alloc()` before they move;
  `set_cpus_allowed_dl()` subtracts it from the source afterwards.
- `dl_rebuild_rd_accounting()` is in `kernel/cgroup/cpuset.c`; it calls
  `dl_clear_root_domain_cpu()`, then `dl_add_task_root_domain()` per task.
