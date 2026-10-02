- `bioset_init()`: creates the workqueue with `WQ_MEM_RECLAIM | WQ_PERCPU`.
- `rescue_lock`, `rescue_list` and `rescue_work`: initialised for every
  bioset; only `rescue_workqueue` depends on `BIOSET_NEED_RESCUER`.
- `bio_alloc_bioset()`: tests neither `bs->rescue_workqueue` nor
  `current->bio_list`. It calls `punt_bios_to_rescuer()` every time it enters
  the slow path with a mask that has `__GFP_DIRECT_RECLAIM`.
- `punt_bios_to_rescuer()`: makes those tests on its first line and returns
  silently; it has no `WARN_ON_ONCE()`.
- Bioset without a rescuer: the only difference is that nothing leaves
  `current->bio_list` before `mempool_alloc()` may sleep. The weakened mask
  of the first attempt is the same for both kinds of bioset.
- Time of the punt: after the slab attempt failed and before
  `mempool_alloc()` is called, so bios are punted even when the mempool
  reserve still has elements.
- One punt covers both `mempool_alloc()` calls, on `bs->bio_pool` and on
  `bs->bvec_pool`; it is not repeated for the bvecs.
