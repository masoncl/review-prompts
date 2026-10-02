- **Potentially unsafe usage**: `spin_lock()`, `read_lock()`, `write_lock()`
  or `local_lock()` (any suffix) where preemption or interrupts are disabled
  on RT: after `preempt_disable()`, `local_irq_save()` or `get_cpu_ptr()`,
  under a `raw_spinlock_t` or `bit_spin_lock()`, or in a handler that stays
  in hard interrupt context.
  - Unsafe: when another task or CPU can hold the lock;
    `rtlock_slowlock_locked()` in `kernel/locking/rtmutex.c` then calls
    `schedule_rtlock()`.
  - Safe: when nothing else can run and hold the lock, as under
    `tick_freeze()` and `tick_unfreeze()` in `kernel/time/tick-common.c` once
    `tick_freeze_depth == num_online_cpus()`; `__might_resched()` returns
    early while `system_state > SYSTEM_RUNNING`.
  - Safe: `spin_lock_irqsave()` on its own, as `add_wait_queue()` in
    `kernel/sched/wait.c` does; `rtlock_might_resched()` in
    `kernel/locking/spinlock_rt.c` requires `preempt_count()` zero and
    interrupts enabled, and the RT irq forms disable nothing.
  - Safe: inside `rcu_read_lock()` or a BH-disabled section, as
    `gro_cells_receive()` does; `RTLOCK_RESCHED_OFFSETS` allows the RCU
    depth, and RT `softirq_count()` is kept in `softirq_disable_cnt` of the
    task, not in `preempt_count()`.
  - Safe: `local_lock()` and then `this_cpu_ptr()` in place of
    `get_cpu_ptr()`, as `mlock_folio()` in `mm/mlock.c` does.
- **Potentially unsafe usage**: `kmalloc()` or `kfree()` under a
  `raw_spinlock_t` or with preemption or interrupts disabled on RT.
  - Unsafe: once other tasks or CPUs run and can hold the allocator's locks;
    `list_lock` in `mm/slub.c` is a `spinlock_t`.
  - Safe: in early boot with interrupts still off, as
    `workqueue_init_early()` called from `start_kernel()`; nothing else runs,
    and `__might_resched()` returns while `system_state == SYSTEM_BOOTING`.
  - Safe: `kmalloc_nolock()` and `kfree_nolock()` (not with `pi_lock` of
    `struct task_struct` held), or allocate while holding only a
    `spinlock_t`.
- Detection on RT: `rtlock_might_resched()` reports the preempt-off and
  irq-off cases, and only with `CONFIG_DEBUG_ATOMIC_SLEEP`.
