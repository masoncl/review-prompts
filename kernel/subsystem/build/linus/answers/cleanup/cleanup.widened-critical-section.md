- `__free()` and `CLASS()` variables declared after the new `guard()`: their
  release now runs before the unlock, so a put or free that used to follow the
  unlock call now runs under the lock; `cxlr` in `cxl_add_to_region()` in
  `drivers/cxl/core/region.c` is put before `regions_lock` is dropped.
- A release that takes the same lock: must stay outside the guard;
  `tracepoint_user_put()` in `kernel/trace/trace_fprobe.c` takes
  `tracepoint_user_mutex` itself.
- `scoped_guard()` keeping the old hold time, in-tree: `perf_pmu_unregister()`
  in `kernel/events/core.c` wraps only the `pmu_idr` and list update, then
  calls `synchronize_srcu()` and `perf_pmu_free()` unlocked.
- `tracepoint_user_put()`: frees with `__tracepoint_user_free()` after its
  `scoped_guard()` has ended.
