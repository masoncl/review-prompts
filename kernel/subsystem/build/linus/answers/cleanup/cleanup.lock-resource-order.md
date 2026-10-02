| Case | In-tree code | What to see |
|---|---|---|
| release after unlock, lock inside the object | `cxl_add_to_region()` in `drivers/cxl/core/region.c` | `cxlrd` with `__free(put_cxl_root_decoder)` is declared before `guard(mutex)(&cxlrd->regions_lock)` |
| release after unlock, scoped lock | `cxl_mem_probe()` in `drivers/cxl/mem.c` | `parent_port` with `__free(put_cxl_port)`, then `scoped_guard(device, endpoint_parent)` |
| both orders in one function | `perf_pmu_register()` in `kernel/events/core.c` | `pmu` with `__free(pmu_unregister)`, then `guard(mutex)(&pmus_lock)`, then `CLASS(idr_alloc, pmu_type)` |

- `cxl_add_to_region()`: the last put reaches `cxl_root_decoder_release()` in
  `drivers/cxl/core/port.c`, which calls `mutex_destroy()` on `regions_lock`
  and `kfree()` on the decoder, so the put has to run after the unlock.
- `cxl_mem_probe()`: the `scoped_guard()` ends before the function does, so
  the lock is dropped before `parent_port` is put whatever the declaration
  order.
- `perf_pmu_register()`, release under the lock: the `CLASS(idr_alloc,
  pmu_type)` destructor calls `idr_remove()` on `pmu_idr` before `pmus_lock`
  is dropped; the `idr_cmpxchg()` and `idr_remove()` calls on `pmu_idr` in
  that file are under `pmus_lock` too.
- `perf_pmu_register()`, release after unlock: `perf_pmu_free()` runs after
  `pmus_lock` is dropped, as it does in `perf_pmu_unregister()`.
- Release under the lock with a `__free()` variable: shown by the corrected
  `init()` in the DOC comment of `include/linux/cleanup.h`, which is not
  compiled; the `perf_pmu_register()` case uses `CLASS()`.
- `__free()` after a `guard()` in-tree: for example `cxlr` in
  `cxl_add_to_region()`, a reference whose put does not need the lock.
