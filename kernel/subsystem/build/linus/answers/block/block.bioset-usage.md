- `BIOSET_NEED_RESCUER`: only `drivers/md/bcache/super.c` passes it. The
  biosets of dm and md, `fs_bio_set` and the `bio_split` bioset of
  `struct gendisk` have no rescuer, so the rescuer paragraph of the comment
  above `bio_alloc_bioset()` does not apply to them.
- **Potentially unsafe usage**: under `->submit_bio`, a sleeping allocation
  from a bioset after a bio from the same bioset was submitted in the same
  call.
  - Unsafe: when the bioset has no `BIOSET_NEED_RESCUER`. The earlier bio
    stays on `current->bio_list` until `->submit_bio` returns,
    `punt_bios_to_rescuer()` moves nothing, and `mempool_alloc()` can wait
    for an element that only the completion of that bio frees.
  - Safe: one allocation per `->submit_bio` call, with the remainder
    resubmitted, as `raid0_make_request()` does through
    `bio_submit_split_bioset()` for a bio that has no `REQ_PREFLUSH` and is
    not `REQ_OP_DISCARD`. `__submit_bio_noacct()` in `block/blk-core.c` runs
    the bios for lower queues before it re-enters `->submit_bio` for the
    remainder. The comment above `bio_alloc_bioset()` defines the
    requirement.
  - Safe: a bioset with `BIOSET_NEED_RESCUER` and a mask that has
    `__GFP_DIRECT_RECLAIM`, as `cache_lookup_fn()` in
    `drivers/md/bcache/request.c` does. `punt_bios_to_rescuer()` hands the
    parked bios of that bioset to `bio_alloc_rescue()`.
- Front pad contents: not initialised. `bio_alloc_bioset()` runs `bio_init()`
  on the bio only, and the memory may come from the per-cpu cache, the slab
  or the mempool, so the caller sets every field it reads.
