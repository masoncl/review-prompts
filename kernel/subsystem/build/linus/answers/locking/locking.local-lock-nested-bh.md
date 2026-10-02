- `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`: has no `default` in
  `kernel/Kconfig.preempt`, so it is off unless selected by hand.
- Option off: first-level `__local_bh_disable_ip()` from `preemptible()`
  code calls `migrate_disable()` and `rcu_read_lock()` and takes no lock;
  BH-disabled sections of different tasks on one CPU interleave.
- Option on: first-level `__local_bh_disable_ip()` from `preemptible()` code
  takes `local_lock(&softirq_ctrl.lock)`, which serialises them.
- Softirq handlers with the option off: can run on the CPU while another
  task is preempted inside its BH-disabled section; `__local_bh_enable_ip()`
  decides from `current->softirq_disable_cnt`.
- `Documentation/locking/locktypes.rst` on `_bh` ("use a per-CPU lock for
  serialization"): true only with `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`.
- `local_lock_nested_bh()` on RT: takes the per-CPU `spinlock_t` with
  `spin_lock()`; with the option off `local_bh_disable()` adds no
  serialisation to it.
- RT `__local_lock_nested_bh()`: omits the `migrate_disable()` that
  `__local_lock()` does before `this_cpu_ptr()`; the caller's BH-disabled
  state pins the CPU. `rt_spin_lock()` still calls `migrate_disable()`.
- `lockdep_assert_in_softirq()`: the precondition check; needs
  `in_softirq()` and neither `in_hardirq()` nor `in_nmi()`, and exists only
  with `CONFIG_PROVE_LOCKING`.
- `__local_lock_nested_bh()`: takes an already resolved pointer instead of a
  `__percpu` one, as `gro_cell_poll()` in `net/core/gro_cells.c` does.
- Allocated per-CPU data: call `local_lock_init()` on each CPU's lock, as
  `gro_cells_init()` does; static data uses `INIT_LOCAL_LOCK()`.
- **Potentially unsafe usage**: per-CPU data touched under
  `local_bh_disable()` or in softirq with no lock of its own, on RT.
  - Unsafe: without `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`, when the data needs
    more than one access to stay consistent; `__local_bh_disable_ip()` then
    takes no lock, so another task can run a BH-disabled section on the CPU
    in between.
  - Safe: a `local_lock_t` in the structure, taken with
    `local_lock_nested_bh()` on every access, as `napi_alloc_cache` in
    `net/core/skbuff.c` is.
  - Safe: a single `this_cpu_*()` operation, as `netdev_core_stats_inc()` in
    `net/core/dev.c`; the generic `this_cpu_generic_to_op()` runs under
    `raw_local_irq_save()`.
