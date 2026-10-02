- Write side: `rwsem_write_kill` is `down_write_killable()`, so only a fatal
  signal ends the wait; the read side `rwsem_read_intr` and `mutex_intr` end on
  any signal.
- `TASK_INTERRUPTIBLE` passed to `attach_target()`: selects `rwsem_write_kill`
  in `__attach_target()`, a killable wait, not an interruptible one.
- `__attach_target()` killable branch: `cxl_rwsem.dpa` is still taken with an
  unconditional `guard(rwsem_read)` after the conditional region lock.
- `cxl_rwsem.dpa` for write: never taken conditionally; `__cxl_dpa_alloc()`,
  `cxl_dpa_free()` and `cxl_dpa_set_part()` in `drivers/cxl/core/hdm.c` use
  `guard(rwsem_write)` even when reached from `dpa_size_store()` and
  `mode_store()`.
- `cxl_rwsem.dpa` conditional holds: all are `rwsem_read_intr`, taken after
  `cxl_rwsem.region` with the same class, for example `cxl_inject_poison()`.
- Sysfs show handlers with an unconditional `guard(rwsem_read)`: for example
  `target_list_show()`, `decoders_committed_show()` and `dpa_resource_show()`
  in `drivers/cxl/core/port.c`.
- `regions_lock` in sysfs: `create_region_store()` and `delete_region_store()`
  take it with `ACQUIRE(mutex_intr, ...)`.
- `DETACH_INVALIDATE`: the only mode that makes `cxl_decoder_detach()` lock
  unconditionally, and `cxld_unregister()` in `drivers/cxl/core/port.c` is its
  only caller; `detach_target()` passes `DETACH_ONLY` and can return `-EINTR`.
- Other unconditional write holds of `cxl_rwsem.region`, apart from the second
  acquisition in `commit_store()`, are enumeration paths, for example
  `__construct_region()`, `decoder_populate_targets()` and
  `init_hdm_decoder()`; search `guard(rwsem_write)(&cxl_rwsem.region)` for the
  rest.
- **Potentially unsafe usage**: `device_release_driver()`, `device_del()` or
  `device_attach()` on a region while a guard is still in scope.
  - Unsafe: in the scope of `cxl_rwsem.region`, read or write, conditional or
    not; `cxl_region_can_probe()` takes that lock under the region's device
    lock.
  - Safe: after the scope has closed, as `cxl_decoder_detach()` does by putting
    each acquisition in its own braces, and as `commit_store()` does by locking
    inside `queue_reset()`.
  - Safe: in the scope of `regions_lock` alone, as `delete_region_store()` does
    through `unregister_region()`; `cxl_region_can_probe()` does not take
    `regions_lock`.
- **Unsafe usage**: a killable or interruptible acquisition on a path that
  cannot return or retry the error; on failure `cxl_decoder_detach()` returns
  before `__cxl_decoder_detach()` runs and the decoder stays attached.
  - Safe: `DETACH_INVALIDATE`, as `cxld_unregister()` passes.
  - Safe: `TASK_UNINTERRUPTIBLE`, as `cxl_add_to_region()` passes to
    `attach_target()`.
  - Safe: a plain `guard(rwsem_write)` after `queue_reset()` may have set
    `CXL_CONFIG_RESET_PENDING`, as the second acquisition in `commit_store()`.
