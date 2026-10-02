- `CONFIG_SCHED_CACHE`: exists in `init/Kconfig`, default y, depends on SMP;
  code is mainly in `kernel/sched/fair.c` and `kernel/sched/topology.c`.
- Runtime gate: `sched_cache_enabled()` tests the static key
  `sched_cache_active`; it is on only with more than one LLC
  (`sched_cache_present`) and `sysctl_sched_cache_user` set (debugfs
  `llc_balancing/enabled`).
- Preference: one `struct sched_cache_group` per process; `grp->cpu` is
  chosen in `task_cache_work()`, and `account_mm_sched()` copies its LLC
  into `p->preferred_llc`.
- No preference (`-1`): kernel threads, single-threaded processes and
  processes with too many active threads (`invalid_llc_nr()`), a footprint
  above the LLC size (`exceed_llc_capacity()`), a stale epoch, or a conflict
  with `p->numa_preferred_nid`.
- It changes placement in load balancing only; the decisions are made in:
  - `can_migrate_task()`: `migrate_degrades_llc()` refuses a move that
    breaks the preference, when NUMA locality is neutral.
  - `update_sg_lb_stats()`: `llc_balance()` marks `group_llc_balance`;
    `calculate_imbalance()` then pulls one task with `migrate_llc_task`.
  - `need_active_balance()`: `alb_break_llc()` vetoes, and
    `migrate_llc_task` makes it return 1; `alb_stop_fn()` then picks
    `active_load_balance_llc_cpu_stop()`.
- `can_migrate_llc()`: the policy; returns `mig_forbid`, `mig_llc` or
  `mig_unrestricted` from LLC utilisation.
- `LBF_LLC_PINNED`: set when a task is refused for LLC reasons and the
  migration type is not `migrate_llc_task`, so that `sched_balance_rq()`
  does not raise `nr_balance_failed`.
- Override: both `migrate_degrades_llc()` and `llc_balance()` give up once
  `nr_balance_failed` reaches `cache_nice_tries + 1`.
- `task_has_sched_core()` tasks: exempt in `migrate_degrades_llc()`.
- Newly idle balance: `record_sg_llc_stats()` skips it, so LLC utilisation
  is refreshed only by a balance that is not newly idle; the migration
  filter still runs.
- Left alone: wakeup placement (`select_task_rq_fair()`, `wake_affine()`,
  `select_idle_sibling()`), fork and exec placement
  (`sched_balance_find_dst_cpu()`) and `task_numa_migrate()`; none reads
  `p->preferred_llc` or `grp->cpu`.
- Counters: `rq->nr_pref_llc_running` and `sd->llc_counts` are kept by
  `account_llc_enqueue()` and `account_llc_dequeue()`; `set_delayed()` and
  `clear_delayed()` adjust the first for delayed tasks.
