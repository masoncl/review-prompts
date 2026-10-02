- Order, outermost first: memdev or port device lock, `cxlrd->regions_lock`,
  the region's own device lock, `cxl_rwsem.region`, `cxl_rwsem.dpa`.
- Region device lock inside `regions_lock`: `device_attach()` in
  `cxl_add_to_region()` and `device_del()` in `unregister_region()` both run
  with `regions_lock` held.
- Region device lock outside `cxl_rwsem.region`: `cxl_region_can_probe()` takes
  `cxl_rwsem.region` for read from `cxl_region_probe()`.
- `cxl_add_to_region()`: `regions_lock` is a `guard(mutex)` held to the end of
  the function, so everything from `cxl_find_region_by_range()` on runs under
  it.
- Calls under `regions_lock`, in order:
  - `cxl_find_region_by_range()`; its callback `match_region_by_range()` takes
    `cxl_rwsem.region` for read per child.
  - `construct_region()` when no region matched: `__create_region()` adds the
    region device without `cxl_rwsem.region`, then `__construct_region()` takes
    it for write.
  - `attach_target()` with `TASK_UNINTERRUPTIBLE`: `cxl_rwsem.region` write,
    then `cxl_rwsem.dpa` read; the return value is ignored.
  - `scoped_guard(rwsem_read, &cxl_rwsem.region)` to read `p->state`.
  - `device_attach()` on the region when the state is `CXL_CONFIG_COMMIT`, with
    no `cxl_rwsem` member held.
  - the `put_device()` from `__free(put_cxl_region)`, which runs before the
    mutex is released.
