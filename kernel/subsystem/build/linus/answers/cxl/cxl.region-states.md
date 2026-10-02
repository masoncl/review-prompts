- `size` write (`alloc_hpa()`): the only store that moves `CXL_CONFIG_IDLE` to
  `CXL_CONFIG_INTERLEAVE_ACTIVE`; `set_interleave_ways()` and
  `set_interleave_granularity()` never write `p->state`.
- `alloc_hpa()`: returns `-ENXIO` unless ways, granularity and (for
  `CXL_PARTMODE_PMEM`) the uuid are already set.
- `uuid_store()` and `free_hpa()` (size 0): the state test is
  `p->state >= CXL_CONFIG_ACTIVE` (`-EBUSY`), so both work in
  `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `uuid_store()`: writing the uuid already set returns success before the
  state test.
- `store_targetN()` with an empty write: `__cxl_decoder_detach()` moves any
  state `> CXL_CONFIG_ACTIVE` (`CXL_CONFIG_COMMIT` or
  `CXL_CONFIG_RESET_PENDING`) to `CXL_CONFIG_ACTIVE`, then
  `CXL_CONFIG_ACTIVE` to `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `commit_store()` with 0: the first test is `CXL_REGION_F_LOCK`, read with no
  lock held; set returns `-EPERM` before `queue_reset()`.
- `queue_reset()` on a region below `CXL_CONFIG_COMMIT`: returns 0 and leaves
  the state alone; `device_release_driver()` still runs and the write succeeds.
- `commit_store()` locks: `queue_reset()` takes `cxl_rwsem.region` killable;
  after the release it is taken with `guard(rwsem_write)`, which cannot fail.
- After the release nothing can fail: `cxl_region_decode_reset()` returns void
  and the state becomes `CXL_CONFIG_ACTIVE` whenever it is still
  `CXL_CONFIG_RESET_PENDING`.
- **Unsafe usage**: moving `p->state` below `CXL_CONFIG_COMMIT` and leaving
  the region driver bound.
  - Unsafe: `cxl_region_perf_attrs_callback()` and
    `cxl_region_calculate_adistance()` read `cxlr->params.res` with no lock
    while the driver is bound.
  - Safe: change the state under the write lock, drop the lock, then call
    `device_release_driver()`, as `commit_store()` does, and as
    `cxl_decoder_detach()` does when `__cxl_decoder_detach()` returns the
    region; `cxl_region_can_probe()` refuses a rebind below
    `CXL_CONFIG_COMMIT`.
