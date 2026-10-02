- `static_key_slow_inc()` and `static_key_slow_dec()`: take `cpus_read_lock()`
  on every call, whatever the count. Only `jump_label_mutex` is skipped when
  the count is already above the threshold.
- `static_key_enable()` on an enabled key: takes `cpus_read_lock()`, returns
  before `jump_label_lock()`.
- `static_key_fast_inc_not_disabled()`: takes no lock.
- `__static_key_slow_dec_deferred()`: no lock while the count stays above one;
  otherwise the delayed work takes `cpus_read_lock()`.
- `static_branch_enable_cpuslocked()` and `static_key_enable_cpuslocked()`:
  still take `jump_label_mutex` unless the key is already enabled; on x86 the
  patching in `arch/x86/kernel/jump_label.c` also takes `text_mutex`.
- `lockdep_assert_cpus_held()`: returns without checking while
  `system_state < SYSTEM_RUNNING`.
- Without `CONFIG_JUMP_LABEL`: every operation is a plain atomic in
  `include/linux/jump_label.h`, no lock; the `_cpuslocked` names are aliases.
- Without `CONFIG_HOTPLUG_CPU`: `cpus_read_lock()` is empty.
- `cpus_read_lock()`: calls `might_sleep()` and is tracked by lockdep as a
  non-recursive read (`percpu_down_read_internal()`).
- **Unsafe usage**: a static key enable, disable, inc or dec, in the plain or
  the `_cpuslocked` form, on a path that a page allocation or reclaim can
  reach.
  - Unsafe: `jump_label_module_notify()` holds `cpus_read_lock()` and
    `jump_label_mutex` across `kzalloc_obj()` with `GFP_KERNEL`; an operation
    reached from that allocation takes `jump_label_mutex` again.
  - Unsafe: allocator callers may be atomic; the operation sleeps.
  - Safe: test plain state, as `cond_accept_memory()` does with
    `list_empty()` on `zone->unaccepted_pages`.
  - Safe: defer to a work item, as `toggle_allocation_gate()` in
    `mm/kfence/core.c` and `net_enable_timestamp()` in `net/core/dev.c` do.
- **Potentially unsafe usage**: `static_branch_enable()` or another
  non-`_cpuslocked` form.
  - Unsafe: when the caller already holds `cpus_read_lock()`, for example
    under `mem_hotplug_begin()` or in a CPU hotplug callback.
  - Safe: caller holds no hotplug lock and can sleep, as `netstamp_clear()`.
  - Safe: caller holds `cpus_read_lock()` and uses the `_cpuslocked` form, as
    `lru_gen_change_state()` in `mm/vmscan.c` does, and as
    `cpuset_css_online()` does through `cpuset_inc()`.
- **Unsafe usage**: a non-`_cpuslocked` static key operation while holding
  `pcp_batch_high_lock`, that is between `zone_pcp_disable()` and
  `zone_pcp_enable()`.
  - Unsafe: `page_alloc_cpu_online()` takes `pcp_batch_high_lock` in
    `zone_pcp_update()` with `cpus_write_lock()` held by `_cpu_up()`.
  - Safe: the `_cpuslocked` form, with `cpus_read_lock()` taken before
    `zone_pcp_disable()`; `memory_block_offline()` takes it with
    `mem_hotplug_begin()` before `offline_pages()`.
