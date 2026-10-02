- `can_spin_trylock()` in `mm/internal.h`: the run-time test; false on
  PREEMPT_RT in NMI or hardirq, false on `!CONFIG_SMP` in NMI, true
  otherwise, including with interrupts disabled.
- `free_one_page()` in `mm/page_alloc.c`: decides at run time; with
  `FPI_NOLOCK` it needs `can_spin_trylock()` and `spin_trylock_irqsave()` to
  succeed, else it queues the page on `zone->trylock_free_pages`.
- `alloc_nolock_allowed()` in `mm/page_alloc.c` and
  `__kmalloc_nolock_noprof()` in `mm/slub.c`: return failure when
  `can_spin_trylock()` is false.
- There is no ALLOC_TRYLOCK, FPI_TRYLOCK, pcp_trylock_prepare() or
  try_alloc_pages() here; the names are `ALLOC_NOLOCK`, `FPI_NOLOCK` and
  `alloc_pages_nolock()`, and on `!CONFIG_SMP` `pcp_spin_trylock()` is
  defined as `NULL`.
- `gfpflags_allow_spinning()`: not what the page allocator or slub test;
  they test `ALLOC_NOLOCK` and `alloc_flags_allow_spinning()`.
- `consume_stock()` in `mm/memcontrol.c`: always uses `local_trylock()`.
- `__bpf_ringbuf_reserve()`: takes `raw_res_spin_lock_irqsave()` and fails
  when that fails; it has no `in_nmi()` test.
- `local_lock_is_locked()`: defined, no caller in this tree.
- `local_trylock()` and `local_trylock_irqsave()` on PREEMPT_RT: may be
  called in NMI and hardirq; they return 0 there without touching the lock.
- **Potentially unsafe usage**: `spin_trylock()` on a `spinlock_t` from
  hardirq or NMI.
  - Unsafe: on PREEMPT_RT; `rt_spin_trylock()` records `current`, the
    interrupted task, as owner. `write_trylock()` on a `rwlock_t` is unsafe
    there in the same way: `rt_write_trylock()` takes the rtmutex for
    `current` through `rwbase_write_trylock()` in
    `kernel/locking/rwbase_rt.c`.
  - Unsafe: on `!CONFIG_SMP` without `CONFIG_DEBUG_SPINLOCK`, from NMI, or
    from hardirq when a holder leaves interrupts enabled; the trylock in
    `include/linux/spinlock_api_up.h` returns 1 without testing anything.
  - Safe: after `can_spin_trylock()` returned true, on a lock that every
    holder takes with interrupts disabled, as `free_one_page()` does with
    `zone->lock`.
  - Safe: on PREEMPT_RT with interrupts disabled or a `raw_spinlock_t` other
    than `pi_lock` of `struct task_struct` held, outside hardirq and NMI;
    `can_spin_trylock()` allows it. `rt_spin_trylock()` has no might-sleep
    check, and `rt_mutex_slowtrylock()` in `kernel/locking/rtmutex.c` takes
    `wait_lock` with `raw_spin_lock_irqsave()`.
