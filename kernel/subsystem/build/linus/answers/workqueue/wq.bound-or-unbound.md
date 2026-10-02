- Neither `WQ_PERCPU` nor `WQ_UNBOUND`: `__alloc_workqueue()` does
  `WARN_ONCE()`, sets `WQ_PERCPU`, and the allocation succeeds.
- Both flags: `WARN_ONCE()`, `WQ_PERCPU` is cleared, the workqueue is unbound,
  and the allocation succeeds.
- Each `WARN_ONCE()` is one call site, so only the first offending workqueue
  in a boot is reported; a clean log does not show a later caller is right.
- After `__alloc_workqueue()` exactly one of the two flags is set in
  `wq->flags`; the rest of `kernel/workqueue.c` tests only `WQ_UNBOUND`.
- `WQ_BH` without `WQ_PERCPU`: accepted, and trips the neither-flag warning;
  `system_bh_wq` is created with `WQ_BH | WQ_PERCPU`.
- `WQ_POWER_EFFICIENT` with `wq_power_efficient` set: `WQ_PERCPU` is replaced
  by `WQ_UNBOUND` before the both-flags test, so no warning.
- `wq_power_efficient`: also forced true in `workqueue_init_early()` when
  `housekeeping_enabled(HK_TYPE_TICK)`, before the system workqueues are
  created.
- Default affinity scope of an unbound workqueue: `wq_affn_dfl` starts as
  `WQ_AFFN_CACHE_SHARD`, not `WQ_AFFN_CACHE`.
