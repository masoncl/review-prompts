# Block Layer Subsystem

## Main structures

### Objects and how they relate

- `struct blk_plug`: holds requests only (`mq_list`), plus preallocated
  requests (`cached_rqs`) and unplug callbacks (`cb_list`); it never holds
  bios. A bio-based driver batches by registering a callback with
  `blk_check_plugged()`.
- `struct blk_mq_tags` (driver tags): belongs to the `struct blk_mq_tag_set`,
  not to the hctx. `hctx->tags` is a borrowed pointer to `set->tags[i]`, so
  hctx `i` of every queue on the set shares one tag space; with
  `BLK_MQ_F_TAG_HCTX_SHARED` every `set->tags[i]` is `set->shared_tags`.
- `struct elevator_tags` in `block/elevator.h`: owns the scheduler tags of one
  queue. It hangs off `elevator_queue->et`; `hctx->sched_tags` points into it
  (`blk_mq_init_sched()` in `block/blk-mq-sched.c`).
- `struct request` with an elevator attached: the structure comes from the
  queue's scheduler tags (`static_rqs`), not from the tag set.
  `hctx->tags->rqs[rq->tag]` is pointed at it only in
  `blk_mq_start_request()`.
- `struct blk_mq_ctx` and the elevator are alternatives, not stages: see
  `blk_mq_insert_request()` in `block/blk-mq.c`. With `q->elevator` set a
  request goes to the elevator and never onto `ctx->rq_lists`; flush and
  passthrough requests go straight to `hctx->dispatch` in both cases.
- `q->queue_hw_ctx`: an RCU-protected array of hctx pointers, read through
  `queue_hctx()`. There is no hctx_table xarray in this tree.
- `struct gendisk` and its queue: the disk always holds a queue reference
  (dropped in `disk_release()`), but owns the queue only when `GD_OWNS_QUEUE`
  is set. `blk_mq_alloc_disk_for_queue()` (used by `sd_probe()` and
  `sr_probe()`) does not set it; `__del_gendisk()` then unfreezes the queue so
  passthrough keeps working, instead of leaving it frozen and exiting it.
- `struct gendisk` has no refcount of its own: `disk_to_dev()` is
  `part0->bd_device`, and the gendisk memory is freed by `bdev_free_inode()`
  of the whole-disk bdev.
- `struct queue_limits`: embedded as `q->limits`, and `struct blk_integrity` is
  embedded inside it, so an integrity profile change is a limits update.
- `struct blkcg_gq` and `struct rq_qos`: both point at or hang off the queue
  but are set up and torn down with the disk (`blkcg_init_disk()`,
  `blkcg_exit_disk()`, `rq_qos_add()`, `rq_qos_exit()`); a queue with no
  `struct gendisk` has neither.
- Zoned disks never have partitions: `__add_disk()` in `block/genhd.c` sets
  `GENHD_FL_NO_PART`. Partition remap (`blk_partition_remap()`) runs in
  `submit_bio_noacct()`, before any zone write plugging.
- `struct blk_zone_wplug`: private to `block/blk-zoned.c`. Plugs are allocated
  on demand into `disk->zone_wplugs_hash` for zones being written; there is
  not one per zone. A plugged bio holds its own `q_usage_counter` reference.
- Zone write plugging on a bio-based disk: happens only if the driver calls
  `blk_zone_plug_bio()`, as `dm_zone_plug_bio()` does; blk-mq calls it from
  `blk_mq_submit_bio()` after the split and the merge attempt.
- `QUEUE_FLAG_ZONED_QD1_WRITES`: when set, plugged zone writes are issued by
  one kthread per disk, `disk->zone_wplugs_worker`, which waits for each bio
  to complete before issuing the next, instead of by per-plug work items.

## Where to look

### Core files

| Job | In this tree |
|---|---|
| bio submission | `block/error-injection.c` (`CONFIG_BLK_ERROR_INJECTION`) is also on this path: `blk_error_inject()` is the first call in `submit_bio_noacct_nocheck()` in `block/blk-core.c` |
| splitting | `__bio_split_to_limits()` is `static inline` in `block/blk.h`, not in `block/blk-merge.c`; `bio_split_rw_at()` is `static inline` in `include/linux/blkdev.h`; `bio_split()` is in `block/bio.c` |
| request to scatterlist / DMA | `block/blk-mq-dma.c` (always built): `__blk_rq_map_sg()` and, under `CONFIG_BLK_DEV_INTEGRITY`, `blk_rq_map_integrity_sg()`; `blk_rq_map_sg()` is an inline wrapper in `include/linux/blk-mq.h`; none of these is in `block/blk-merge.c` |
| blk-mq CPU-to-queue mapping | `block/blk-mq-cpumap.c`; block/blk-mq-pci.c, block/blk-mq-virtio.c, block/blk-mq-rdma.c and block/blk-mq-map.c do not exist; `blk_mq_map_hw_queues()` takes a `struct device` and serves PCI and virtio drivers alike |
| tags | no block/blk-mq-tag.h: `struct blk_mq_tags` is in `include/linux/blk-mq.h`, prototypes in `block/blk-mq.h`; scheduler tag sets are allocated by `blk_mq_alloc_sched_tags()` in `block/blk-mq-sched.c` into `struct elevator_tags` (`block/elevator.h`) |
| scheduler glue | header is `block/elevator.h`; include/linux/elevator.h does not exist; `block/kyber-iosched.c` is present |
| flush machinery | `struct blk_flush_queue` is in `block/blk.h`; there is no fq_flush_rq identifier |
| zoned support | no block/blk-mq-debugfs-zoned.c; the debugfs `zone_wplugs` handler `queue_zone_wplugs_show()` is in `block/blk-zoned.c` |
| integrity | five files under `CONFIG_BLK_DEV_INTEGRITY`; the two easily missed are `block/bio-integrity-auto.c` (`bio_integrity_prep()`, block-layer automatic generate/verify) and `block/bio-integrity-fs.c` (`fs_bio_integrity_generate()`, `fs_bio_integrity_verify()`); `bio_integrity_generate()` and `bio_integrity_verify()` themselves are in `block/t10-pi.c` |
| rq_qos policies | exactly the three in `enum rq_qos_id` in `block/blk-rq-qos.h`; `block/blk-ioprio.c` has no rq_qos hook, it is entered through `blkcg_set_ioprio()` from `bio_set_ioprio()` in `block/blk-core.c` |
| cgroup support | also `block/blk-cgroup-fc-appid.c` (`CONFIG_BLK_CGROUP_FC_APPID`) |
| disk object | `struct gendisk` is in `include/linux/blkdev.h`; include/linux/genhd.h does not exist; `bd_link_disk_holder()` is in `block/holder.c`, built only with `CONFIG_BLOCK_HOLDER_DEPRECATED`, not in `block/bdev.c` |
| block device object | no blkdev_get_by_dev() or blkdev_get_by_path() is defined (blkdev_get_by_dev survives only in comments); the openers are `bdev_file_open_by_dev()`, `bdev_file_open_by_path()` and `bdev_open()` in `block/bdev.c` |
| SCSI ioctls | no scsi_ioctl.c in `block/`; it is `drivers/scsi/scsi_ioctl.c` |

## Operations and bio data

**Operations and their payload**

- Zone management ops: `REQ_OP_ZONE_OPEN` is 11, `REQ_OP_ZONE_CLOSE` 13,
  `REQ_OP_ZONE_FINISH` 15, `REQ_OP_ZONE_RESET` 17, `REQ_OP_ZONE_RESET_ALL` 19.
- All five zone management ops are odd, so `op_is_write()` is true and
  `bio_data_dir()` is `WRITE` for each, although none carries data.
- `REQ_OP_ZONE_APPEND`: value 7.
- `op_is_write()` is false only for `REQ_OP_READ`, `REQ_OP_FLUSH` and
  `REQ_OP_DRV_IN`.
- `REQ_OP_FLUSH` in a bio: `submit_bio_noacct()` in `block/blk-core.c` ends
  the bio with `BLK_STS_NOTSUPP`.
- `REQ_OP_DRV_IN` and `REQ_OP_DRV_OUT` in a bio: `submit_bio_noacct()` ends
  the bio with `BLK_STS_NOTSUPP` too.
- `REQ_PREFLUSH` or `REQ_FUA` on a bio: `submit_bio_noacct()` accepts them
  only with `REQ_OP_WRITE` or `REQ_OP_ZONE_APPEND`; with any other op it warns
  once and fails the bio.

**Bio iteration helpers**

- There is no bio_last_bvec_all() in this tree.
- `bio_first_bvec_all()`: the only helper in `include/linux/bio.h` that tests
  `BIO_CLONED`.
- Helpers that reach that test through `bio_first_bvec_all()`:
  `bio_first_page_all()`, `bio_first_folio_all()`, `bio_first_folio()`,
  `bio_for_each_folio_all()`, `bio_for_each_bvec_all()`.
- `bio_for_each_segment_all()`: no `BIO_CLONED` test; `bio_next_segment()`
  only compares the index with `bi_vcnt`.
- `bio_first_bvec_all()` on a flagged bio: warns once and still returns
  `bi_io_vec`.
- `bi_vcnt` in a clone from `bio_alloc_clone()` or `bio_init_clone()`: 0, so
  `bio_for_each_segment_all()` on a clone visits nothing and reports nothing.
- `bio_iov_iter_set()` in `block/bio.c` (there is no bio_iov_bvec_set() here):
  points `bi_io_vec` at the caller's `ITER_BVEC` array, sets `BIO_CLONED` and
  does not set `bi_vcnt`, so the submitter of such a bio cannot use the "_all"
  helpers on it either.
- There is no bio_for_each_folio() here; `bio_for_each_folio_all()` is the
  only folio iterator and it is for the owner.
- There is no bi_bvec_done here; the offset into the current bvec is
  `bi_offset` in `struct bvec_iter`.
- There is no __blk_bios_map_sg() here.
- **Potentially unsafe usage**: reading `bi_io_vec` or `bi_vcnt`, or calling
  an "_all" helper.
  - Unsafe: on a bio received through `->submit_bio` or in a request, from
    index 0 or bounded by `bi_vcnt`. The bio may be the remainder that
    `bio_split()` left: `BIO_CLONED` is clear and `bi_vcnt` is unchanged, but
    `bi_iter` was advanced, so the walk covers the pages of the split-off
    front and nothing warns.
  - Safe: on a bio the caller allocated and filled itself, as
    `mpage_read_end_io()` in `fs/mpage.c` does; the comment above
    `bio_for_each_segment_all()` and the test in `bio_first_bvec_all()` state
    the requirement.
  - Safe: reading `bi_io_vec` at the position `bi_iter` gives, with
    `__bvec_iter_bvec(bio->bi_io_vec, bio->bi_iter)` and `bi_iter.bi_offset`,
    as `lo_rw_aio()` in `drivers/block/loop.c` does for a single-bio request.

**Bios that carry no data**

- `bio_get_first_bvec()` and `bio_get_last_bvec()`: `static inline` in
  `block/blk-merge.c`; nothing outside that file can call them.
- First bvec at `bi_iter`, callable by a driver: `bio_iovec()` (single page),
  `mp_bvec_iter_bvec(bio->bi_io_vec, bio->bi_iter)` (multi-page), `req_bvec()`
  in `include/linux/blk-mq.h` for a request.
- Last bvec: no helper outside `block/blk-merge.c`; inside a loop,
  `bio_iter_last()` and `rq_iter_last()` tell when the current segment is the
  last.
- `blk_rq_has_data()` in `include/linux/blk-mq.h`: the request form of
  `bio_has_data()`.
- Discard payload: a driver's range table is `rq->special_vec` under
  `RQF_SPECIAL_PAYLOAD`; the discard bio itself holds no bvec.
- `bi_io_vec` is NULL in the discard, secure erase, write zeroes and zone
  management bios that `block/blk-lib.c` and `block/blk-zoned.c` build, and in
  the bio of `blkdev_issue_flush()`.
- `rq->nr_phys_segments` of a discard or secure erase request: nonzero, it
  counts ranges (see `__bio_split_discard()` and `blk_recalc_rq_segments()` in
  `block/blk-merge.c`); it does not show that bvecs exist.
- `REQ_OP_FLUSH` request from `block/blk-flush.c`: `rq->bio` is NULL;
  `__rq_for_each_bio()` tests for that, `req_bvec()` does not.
- **Potentially unsafe usage**: `bio_for_each_segment()`,
  `bio_for_each_bvec()`, `rq_for_each_segment()` or `bio_iovec()` on a bio
  whose op is not known.
  - Unsafe: the loops on a `REQ_OP_DISCARD`, `REQ_OP_SECURE_ERASE` or
    `REQ_OP_WRITE_ZEROES` bio. The loop tests only `bi_size`, which holds the
    range length, so the loop dereferences `bi_io_vec`.
  - Unsafe: `bio_iovec()`, `bio_page()` or `bio_offset()` on a bio with
    `bi_size` 0; they make no size test and dereference `bi_io_vec`.
  - Safe: the loops on a bio with `bi_size` 0; they run zero times.
  - Safe: after `bio_has_data()` returned true, as `blk_rq_cur_bytes()` in
    `include/linux/blk-mq.h` does before `bio_iovec()`.
  - Safe: after a switch on the op, as `do_req_filebacked()` in
    `drivers/block/loop.c` does; only `REQ_OP_READ` and `REQ_OP_WRITE` reach
    `lo_rw_aio()`.
- **Potentially unsafe usage**: `req_bvec()` after testing only
  `blk_rq_nr_phys_segments()`.
  - Unsafe: on a discard or secure erase request without
    `RQF_SPECIAL_PAYLOAD`; the count is nonzero and `req_bvec()` dereferences
    the NULL `bi_io_vec`.
  - Safe: when the driver sets `RQF_SPECIAL_PAYLOAD` on every discard before
    it maps data, as `nvme_setup_discard()` does ahead of `nvme_map_data()` in
    `nvme_prep_rq()`; `req_bvec()` then returns `rq->special_vec`.

## Allocating bios

**Bio allocation guarantees**

- `bio_alloc_bioset()` order of sources, all in its own body in `block/bio.c`
  (there is no bvec_alloc() or bvec_alloc_gfp() in this tree):
  1. Per-cpu cache, `bio_alloc_percpu_cache()`, when `bs->cache` is set and
     `nr_vecs <= BIO_INLINE_VECS`. Never sleeps without
     `CONFIG_DEBUG_KMEMLEAK`.
  2. `kmem_cache_alloc()` on `bs->bio_slab`, not the mempool. Never sleeps.
  3. For `nr_vecs > BIO_INLINE_VECS`, `kmem_cache_alloc()` on the slab chosen
     by `biovec_slab()`. Never sleeps. On failure the bio from step 2 goes
     back with `kmem_cache_free()` and step 4 runs if the mask has
     `__GFP_DIRECT_RECLAIM`.
  4. Slow path, only when steps 1 to 3 gave no bio and the mask has
     `__GFP_DIRECT_RECLAIM`: `punt_bios_to_rescuer()`, then `mempool_alloc()`
     on `bs->bio_pool`, then for `nr_vecs > BIO_INLINE_VECS`
     `mempool_alloc()` on `bs->bvec_pool`. Both use the caller's original
     mask and may sleep.
- Mask for steps 2 and 3: when the caller's mask has `__GFP_DIRECT_RECLAIM`,
  `try_alloc_gfp()` strips it and `__GFP_IO` for every bioset, whatever
  `current->bio_list` holds and whether or not there is a rescuer.
- Mask without `__GFP_DIRECT_RECLAIM`: NULL as soon as steps 1 to 3 fail;
  step 4 is not entered and the mempool reserve is never used.
- `nr_vecs > 0` on a bioset without `BIOSET_NEED_BVECS`: `WARN_ON_ONCE()` and
  NULL under any mask, before any allocation, also for
  `nr_vecs <= BIO_INLINE_VECS`.
- `REQ_ALLOC_CACHE` in the caller's `opf` is ignored: `bio_alloc_bioset()`
  sets it when the step 1 condition holds and clears it otherwise and on the
  slow path. Nothing outside `block/bio.c` sets or tests the flag.
- Slow path: the two `mempool_alloc()` results are used unchecked; the code
  relies on `mempool_alloc()` in `mm/mempool.c` not returning NULL when the
  mask has `__GFP_DIRECT_RECLAIM`.
- `bio_alloc_clone()` with a mask that has `__GFP_DIRECT_RECLAIM`: NULL only
  from `bio_integrity_clone()`, which runs when `bio_src` has an integrity
  payload and allocates with `kmalloc_flex()` in `bio_integrity_alloc()`.
- `bio_crypt_clone()` is backed by `mempool_alloc()` in `__bio_crypt_clone()`
  and fails only for a mask without `__GFP_DIRECT_RECLAIM`.

**Bioset rescuer and front pad**

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

**Rescuer workqueue of a bioset**

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

**Integrity payload allocation**

- `bio_integrity_prep()`: `void bio_integrity_prep(struct bio *bio, unsigned
  int action)` in `block/bio-integrity-auto.c`. It has no failure path and
  never ends the bio.
- `blk_mq_submit_bio()`: calls `bio_integrity_action()` after
  `__bio_split_to_limits()`, and calls `bio_integrity_prep()` only for a
  non-zero result.
- `bio_integrity_prep()` makes no checks of its own. On a disk without an
  integrity profile `bio_integrity_alloc_buf()` dereferences the NULL result
  of `blk_get_integrity()`.
- `bio_integrity_action()` in `include/linux/blk-integrity.h` returns 0 when:
  - the disk has no profile, or the bio already has a payload;
  - the bio has a crypt context (`WARN_ON_ONCE()` in
    `__bio_integrity_action()`);
  - the op is not `REQ_OP_READ`, `REQ_OP_WRITE` or `REQ_OP_ZONE_APPEND`;
  - a write or zone append has zero sectors;
  - a read has `BLK_INTEGRITY_NOVERIFY`, or a write has
    `BLK_INTEGRITY_NOGENERATE`, and `metadata_size == pi_tuple_size`.
- `BLK_INTEGRITY_NOVERIFY` or `BLK_INTEGRITY_NOGENERATE` with
  `metadata_size != pi_tuple_size`: a buffer is still attached, without
  `BI_ACT_CHECK`; the write case adds `BI_ACT_ZERO`.
- `__bio_integrity_action()` does not read `csum_type`;
  `bio_integrity_setup_default()` does, when it picks the `BIP_CHECK_FLAGS`
  bits.
- Action bits: `BI_ACT_BUFFER`, `BI_ACT_CHECK`, `BI_ACT_ZERO` in
  `enum bio_integrity_action`. `bio_integrity_prep()` reads only the last
  two and allocates the buffer unconditionally.
- Payload: `mempool_alloc()` on `bid_pool` with `GFP_NOIO`; may sleep, result
  used unchecked. It is not `bio_integrity_alloc()`, and there is no
  bio_integrity_pool in this tree.
- Buffer: `bio_integrity_alloc_buf()` returns `void`. It calls `kmalloc()`
  with the caller's mask plus `__GFP_NOWARN`; `bio_integrity_prep()` passes
  `GFP_NOIO`, direct reclaim included. It then falls back to
  `mempool_alloc()` on `integrity_buf_pool` and sets `BIP_MEMPOOL`. No path
  ends the bio with `BLK_STS_RESOURCE`.
- Size precondition: `bio_integrity_alloc_buf()` does not check the length
  against `BLK_INTEGRITY_MAX_SIZE`, the size of one `integrity_buf_pool`
  element. For `REQ_OP_READ` and `REQ_OP_WRITE` without `REQ_ATOMIC` it
  relies on `blk_validate_integrity_limits()` capping `max_sectors` with
  `max_integrity_io_size()` and on the split that `blk_mq_submit_bio()` does
  first.
- Write generation: there is no blk_integrity_generate() here;
  `bio_integrity_generate()` in `block/t10-pi.c` does that, and runs only if
  `bip_flags` has a `BIP_CHECK_FLAGS` bit.

## Completing, splitting and cloning bios

**Completion and chaining**

- `bio_chain_endio()` in `block/bio.c`: its body is `BUG()`; it is a marker
  only. `bio_endio()` compares `bi_end_io` with it and runs
  `__bio_chain_endio()` instead of calling it.
- **Unsafe usage**: calling the handler of a `bio_chain()` child through the
  `bi_end_io` pointer; it reaches `BUG()` in `bio_chain_endio()`.
  - Safe: `bio_endio()` on the child, which never calls the marker.
  - Safe: the pointer calls in `bio_complete_work_fn()` and
    `bio_complete_batch_cpu_dead()`; `bio_endio()` queues a bio there only
    after its chain test.
- `BIO_CHAIN`: set on the parent by `bio_inc_remaining()`; `bio_chain()` does
  not set it on the child. `bio_remaining_done()` clears it when
  `__bi_remaining` reaches zero.
- `bio_endio()` makes no blk-throttle or blk-crypto call and does not call
  `bio_uninit()` on the bio whose handler it runs; there is no
  blk_throtl_bio_endio() in this tree. Under `CONFIG_BLK_CGROUP` it does
  `blkg_put()` of `bi_blkg`, after the chain jump.
- `BIO_COMPLETE_IN_TASK` (`include/linux/blk_types.h`): when set and
  `bio_in_atomic()` is true, `bio_endio()` does not call `bi_end_io`; it queues
  the bio with `__bio_complete_in_task()` and a per-CPU work item calls the
  handler later. A direct `bi_end_io` call skips this deferral.
- `__bio_complete_in_task()`: links the bio through `bi_next`
  (`bio_list_add()`).
- `bio_in_atomic()` in `include/linux/bio.h`: always true without
  `CONFIG_PREEMPT_COUNT`, so flagged bios are always deferred there.
- `BIO_COMPLETE_IN_TASK` on a chain child: no effect; `bio_endio()` moves to
  the parent before it tests the flag, so the parent's flag decides.
- **Unsafe usage**: `BIO_COMPLETE_IN_TASK` on a bio whose `bi_end_io` is NULL;
  `bio_endio()` tests for NULL only on the non-deferred branch, and
  `bio_complete_work_fn()` calls the pointer unconditionally.
  - Safe: handler set before submission, as `__bh_submit()` in `fs/buffer.c`
    does.
- `bio_complete_in_task()` in `include/linux/bio.h`: for use inside a handler;
  when it returns `true` the bio is queued and the handler runs again from the
  worker, where the flag it set makes the call return `false`.
- `bio_endio_status()` in `include/linux/bio.h`: stores `bi_status`, then calls
  `bio_endio()`; `bio_io_error()` and `bio_wouldblock_error()` wrap it.
- **Unsafe usage**: passing as the child to `bio_chain()` a bio with NULL
  `bi_pool` (set up by `bio_init()` in caller memory, or from `bio_kmalloc()`);
  `__bio_chain_endio()` calls `bio_put()`, and `bio_free()` dereferences
  `bi_pool`.
  - Safe: a child from a `struct bio_set`, as the `bio_split()` result that
    `bio_submit_split_bioset()` chains.
- Parent `bi_status` with several failing children: `__bio_chain_endio()` tests
  and stores without a lock or atomic, so which child's error is kept is not
  defined.
- Parent `bi_status` written by the parent's own completer: not guarded;
  `bio_endio_status()` stores unconditionally, so a success value written
  there replaces a child's error. `blk_update_request()` in `block/blk-mq.c`
  writes `bi_status` only with a nonzero status.

**Splitting and cloning**

- `__bio_clone()` (static, `block/bio.c`) does the copying for
  `bio_alloc_clone()` and `bio_init_clone()`; there is no __bio_clone_fast()
  here.
- `bi_bdev` of a clone: the `bdev` argument, not the source's. With NULL, as
  `alloc_io()` in `drivers/md/dm.c` passes, the clone gets no blkg association
  and no `BIO_REMAPPED`.
- `bi_flags`: not copied. `__bio_clone()` sets `BIO_CLONED`, and carries over
  `BIO_REMAPPED` only when source and clone have the same `bi_bdev`;
  `bio_split()` also carries over `BIO_TRACE_COMPLETION`. There is no
  BIO_THROTTLED; `BIO_BPS_THROTTLED` is not copied.
- `BIO_CLONED` after a split: set on the new front bio only; the remainder
  keeps its own flags.
- Integrity: the clone gets its own `struct bio_integrity_payload` whose
  `bip_vec` points at the source's array. `BIP_BLOCK_INTEGRITY` is not in
  `BIP_CLONE_FLAGS`, so `bio_integrity_endio()` does nothing for the clone.
- Crypt context: a struct copy (`__bio_crypt_clone()`); the `bc_key` pointer
  is shared, so the key must outlive the clone.
- Failure returns differ:

| Function | On failure | Source bio |
|---|---|---|
| `bio_alloc_clone()` | NULL | untouched |
| `bio_init_clone()` | `-ENOMEM` | untouched |
| `bio_split()` | `ERR_PTR()`, never NULL | untouched |
| `bio_submit_split_bioset()` | NULL | already ended |
| `bio_split_to_limits()` | NULL | already ended |

- `bio_split()` errors: `-EINVAL` for `sectors` out of range, for
  `REQ_OP_ZONE_APPEND` (both with `WARN_ON_ONCE()`) and for `REQ_ATOMIC`;
  `-ENOMEM` when the clone fails.
- `bio_split()`: does not chain and does not submit. The caller ties front to
  remainder: with `bio_chain(split, bio)` as `raid10_handle_discard()` in
  `drivers/md/raid10.c` does, or with its own counter as
  `iomap_split_ioend()` in `fs/iomap/ioend.c` does.
- Remainder after `bio_split()`: `bio_advance()` also moves the integrity
  iterator and the crypt DUN (`__bio_advance()`); `bi_bvec_gap_bit` is reset
  to 0.
- `bio_submit_split_bioset()` in `block/blk-merge.c`: chains the front to the
  remainder and submits the remainder itself. It does not go through
  `submit_bio_noacct()`; it calls `should_fail_bio()`, `blk_throtl_bio()`, and,
  when neither took the bio, `submit_bio_noacct_nocheck(bio, true)`, where
  `true` puts the remainder at the head of `current->bio_list[0]` when
  `current->bio_list` is set.
- `REQ_NOMERGE` on the front: added by the static `bio_submit_split()`, not by
  `bio_submit_split_bioset()`; direct callers of `bio_submit_split_bioset()`
  do not get it.
- Split bioset used by `bio_split_to_limits()`: the `bio_split` member of
  `struct gendisk`, reached as `bio->bi_bdev->bd_disk->bio_split`; the
  kerneldoc's "@q->bio_split" does not match the code.
- **Unsafe usage**: submitting or touching the original bio after
  `bio_split_to_limits()` or `bio_submit_split_bioset()` returned a different
  bio or NULL; the remainder is already submitted, or on NULL already ended by
  `bio_endio_status()`.
  - Safe: continue with the returned bio only and return on NULL, as
    `dm_split_and_process_bio()` in `drivers/md/dm.c` does.
- Clones in `drivers/md/dm.c`: made in `alloc_io()` and `alloc_tio()`; there
  is no `clone_bio()` in `drivers/md/dm.c`.

## Entering and freezing a queue

**Queue usage counter**

- Held reference: `blk_mq_freeze_queue_wait()` cannot return. It does not
  mean no freeze has started; `__blk_freeze_queue_start()` kills the counter
  and raises `q->mq_freeze_depth` while references are held.
- `percpu_ref_tryget()` on `q->q_usage_counter`: succeeds on a queue whose
  freeze has started, until the count reaches zero. `blk_mq_timeout_work()`,
  `blk_mq_queue_tag_busy_iter()` and `bio_poll()` enter this way, for example.
- `blk_try_enter_queue()` in `block/blk.h`: the fast path of both
  `blk_queue_enter()` and `bio_queue_enter()`; it is
  `percpu_ref_tryget_live_rcu()` plus a `blk_queue_pm_only()` test.
- `QUEUE_FLAG_DYING` and `GD_DEAD`: tested only after
  `blk_try_enter_queue()` has failed. With a live counter and `q->pm_only`
  zero, both paths succeed without reading either flag.
- Dying queue with `BLK_MQ_REQ_NOWAIT`: `blk_queue_enter()` returns `-EAGAIN`,
  not `-ENODEV`; the NOWAIT test comes before `blk_queue_dying()`.
- Dead disk with `REQ_NOWAIT`: `__bio_queue_enter()` tests `GD_DEAD` first,
  so the bio gets `bio_io_error()` and `-ENODEV`; `bio_wouldblock_error()` is
  only for a disk that is not dead.
- `q->pm_only`: a counter, not `q->rpm_status`; `blk_pre_runtime_suspend()`
  and `scsi_device_quiesce()` raise it.
- `BLK_MQ_REQ_PM` on a pm_only queue: enters unless
  `q->rpm_status == RPM_SUSPENDED`; then it waits like any other caller.
- NOWAIT caller on a pm_only queue: fails with `-EAGAIN` before
  `blk_pm_resume_queue()` runs, so no `pm_request_resume()` is issued.
- After `del_gendisk()` on a disk without `GD_OWNS_QUEUE`: the queue is
  unfrozen, so `bio_queue_enter()` succeeds again despite `GD_DEAD`.
  `__blk_mark_disk_dead()` set the capacity of the whole disk to 0, and
  `bio_check_eod()` in `submit_bio_noacct()` rejects bios to the whole-disk
  bdev that carry sectors and lack `BIO_REMAPPED`; `drop_partition()` does
  not zero a partition's size.
- Lockdep: `blk_queue_enter()` uses `q->q_lockdep_map`; `bio_queue_enter()`
  and `__bio_queue_enter()` use `q->io_lockdep_map`.

**Freeze interface**

- `blk_freeze_queue_start()`: ended with
  `blk_mq_unfreeze_queue_nomemrestore()`. Callers outside `block/blk-mq.c`
  are `nvme_mpath_start_freeze()` and `blk_pre_runtime_suspend()`.
- `nvme_start_freeze()`: calls `blk_freeze_queue_start_non_owner()`, not
  `blk_freeze_queue_start()`; `nvme_unfreeze()` ends it with
  `blk_mq_unfreeze_queue_non_owner()`.
- Owner and non-owner variants: differ only in lockdep. Without
  `CONFIG_LOCKDEP`, `blk_freeze_set_owner()` and `blk_unfreeze_check_owner()`
  return false and the variants behave the same.
- Owner variant unfrozen from another task, with `CONFIG_LOCKDEP`:
  `blk_unfreeze_check_owner()` compares `q->mq_freeze_owner` with `current`
  and returns false, so that unfreeze does not release the maps taken by
  `blk_freeze_acquire_lock()`.
- `blk_queue_start_drain()` in `block/blk-core.c`: the teardown form. It calls
  `__blk_freeze_queue_start(q, current)` and wakes `q->mq_freeze_wq` and tag
  waiters. `__del_gendisk()` calls `blk_freeze_acquire_lock()` by hand;
  `blk_mq_destroy_queue()` ignores the return value.
- Nested `blk_mq_freeze_queue()`: still runs `blk_mq_freeze_queue_wait()`, so
  it blocks until the counter is zero even when the depth was already raised.
- `q->mq_freeze_depth` above zero: means a freeze has started, not that the
  queue has drained.
- `__blk_mq_update_nr_hw_queues()`: its `blk_mq_freeze_queue_nomemsave()` is
  ended inside `elv_update_nr_hw_queues()` in `block/elevator.c`.

**Freeze and quiesce**

- After `blk_mq_freeze_queue_wait()` returns: no request exists, so no
  `queue_rq` call can start; each request holds a counter reference until it
  is freed, in `__blk_mq_free_request()` or `blk_mq_flush_tag_batch()`.
- Still running on a frozen queue: dispatch code that has no request,
  from `hctx->run_work` and `q->requeue_work`. It reads the elevator and
  hctx state without a counter reference.
- `elevator_change()` in `block/elevator.c`: uses three steps, freeze, then
  `blk_mq_cancel_work_sync()`, then `blk_mq_quiesce_queue()` inside
  `elevator_switch()`.
- Bio-based queue (`BD_HAS_SUBMIT_BIO`): `__submit_bio()` holds the reference
  only across `->submit_bio()`. Freeze does not wait for bios the driver
  still holds.
- Quiesce and timeouts: `blk_mq_timeout_work()` is not stopped by quiesce. It
  runs under a counter reference and calls `blk_mq_wait_quiesce_done()` itself.
- `__del_gendisk()`: no quiesce call in its body; the only quiesce on its
  path is the one `elevator_switch()` takes and drops in
  `blk_unregister_queue()`. `rq_qos_exit()` runs on a frozen queue that the
  removal path has not quiesced.
- `blk_mq_quiesce_tagset()`: skips queues with
  `BLK_FEAT_SKIP_TAGSET_QUIESCE` in `q->limits.features`. There is no
  QUEUE_FLAG_SKIP_TAGSET_QUIESCE here.

**Queue state changes under freeze**

- Elevator and `q->nr_requests`: changed under `q->elevator_lock`, not
  `q->sysfs_lock`. `elevator_change()` also asserts
  `set->update_nr_hwq_lock`.
- Lock order around a freeze, as the code takes them:

| Lock | Order | Example |
|---|---|---|
| `set->update_nr_hwq_lock` | before freezing | `elv_iosched_store()` |
| `q->limits_lock` | before freezing | `queue_limits_commit_update_frozen()` |
| `q->rq_qos_mutex` | both orders occur | before freezing: `rq_qos_add()`; after freezing: `ioc_qos_write()`, and `wbt_init()` called from `wbt_set_lat()` |
| `q->elevator_lock` | after freezing | `elevator_change()` |

- `WARN_ON_ONCE(q->mq_freeze_depth == 0)` in `elevator_switch()`: proves a
  freeze was started, not that the queue has drained.
- `__blk_mq_update_nr_hw_queues()`: switches each queue that has an elevator
  to none with `elevator_set_none()`, one freeze per queue, before it freezes
  the whole set. `elv_update_nr_hw_queues()` switches back and unfreezes, per
  queue.
- `elevator_set_default()`: called from `blk_register_queue()`; when it
  selects mq-deadline it goes through `elevator_change()` and freezes. There
  is no elevator_init_mq() here.
- There is no blk_mq_free_queue() here; `blk_mq_exit_queue()` and
  `blk_mq_release()` in `block/blk-mq.c` do the teardown and the free.
- Queue flags: some are flipped under a freeze although the bit operation is
  atomic. `queue_zoned_qd1_writes_store()` freezes and quiesces to flip
  `QUEUE_FLAG_ZONED_QD1_WRITES`; `rq_qos_add()` sets `QUEUE_FLAG_QOS_ENABLED`
  under freeze. Others are flipped with no freeze, for example
  `QUEUE_FLAG_NOMERGES` in `queue_nomerges_store()`.
- `q->queue_hw_ctx`: an RCU-managed array. `queue_hctx()` reads it with
  `rcu_dereference()`; `__blk_mq_realloc_hw_ctxs()` replaces it with
  `rcu_assign_pointer()` and `kfree_rcu_mightsleep()`.
- `set->tags_srcu`: the SRCU that tag iterators hold;
  `blk_mq_queue_tag_busy_iter()` takes it after `percpu_ref_tryget()`.

**Memory allocation while frozen**

- `queue_requests_store()` in `block/blk-sysfs.c`: calls
  `blk_mq_alloc_sched_tags()` before freezing, only when the tags grow.
- `__blk_mq_update_nr_hw_queues()`: before freezing it calls
  `blk_mq_alloc_sched_res_batch()` and `blk_mq_prealloc_tag_set_tags()`.
  There is no blk_mq_alloc_sched_tags_batch() here.
- `__blk_mq_update_nr_hw_queues()`: its `memalloc_noio_save()` scope opens
  before those allocations, so they are NOIO too.
- hctxs in `__blk_mq_update_nr_hw_queues()`: allocated by
  `__blk_mq_realloc_hw_ctxs()` while the queues are frozen, not before;
  `blk_mq_alloc_hctx()` uses `GFP_NOIO`.
- `wbt_set_lat()` in `block/blk-wbt.c`: calls `wbt_alloc()` before
  `blk_mq_freeze_queue()`.
- `q->io_lockdep_map`: the only map primed against `fs_reclaim`, in
  `blk_alloc_queue()`, which records `fs_reclaim` before `io_lockdep_map`
  once, at queue allocation. `q->q_lockdep_map` is not primed. A freeze with
  `q->mq_freeze_disk_dead` set skips `io_lockdep_map` in
  `blk_freeze_acquire_lock()`, so lockdep does not see the reclaim dependency
  for such a freeze.
- NOIO scope: changes allocations only. I/O the caller starts itself must come
  before the freeze; `elv_iosched_store()` loads the scheduler module first.
- debugfs registration: done after unfreezing, under `blk_debugfs_lock()` in
  `block/blk.h`, which opens its own NOIO scope and then takes
  `q->debugfs_mutex`.

**Disk removal**

- `disable_elv_switch()`: runs first in `del_gendisk()` for a blk-mq queue,
  before the NOIO scope; sets `QUEUE_FLAG_NO_ELV_SWITCH`.
- Drain start: `blk_queue_start_drain()` in `__blk_mark_disk_dead()`, which
  `__del_gendisk()` calls under `disk->open_mutex`, before partitions are
  dropped and before any sysfs removal. `__del_gendisk()` has no
  `blk_mq_freeze_queue()` call in its body.
- `GD_ADDED`: not cleared by `__del_gendisk()`.
- Scheduler: torn down in `blk_unregister_queue()` by `elevator_set_none()`,
  before `blk_mq_freeze_queue_wait()` in `__del_gendisk()`.
- `elevator_set_none()`: `elevator_change()` takes a nested
  `blk_mq_freeze_queue()` that waits for the counter to reach zero. For a
  registered blk-mq queue the I/O has drained by the time
  `blk_unregister_queue()` returns.
- `__del_gendisk()` after the wait: `blk_throtl_cancel_bios()`,
  `blk_sync_queue()`, `blk_flush_integrity()`, `blk_mq_cancel_work_sync()`,
  `rq_qos_exit()`. There is no quiesce and no elevator call here.
- End state by `GD_OWNS_QUEUE`:

| | Disk owns the queue | Disk does not |
|---|---|---|
| Freeze | left frozen | `__blk_mq_unfreeze_queue(q, true)` |
| hctxs | `blk_mq_exit_queue()` has run | live |
| `QUEUE_FLAG_DYING` | set | not set by `__del_gendisk()`; `blk_mark_disk_dead()` sets it |

- `blk_mq_destroy_queue()`: does not quiesce, does not call
  `blk_mq_freeze_queue()` on the queue it destroys, and does not call
  `blk_put_queue()`; the caller drops the reference.
- `blk_mq_destroy_queue()`: touches neither the elevator nor rq_qos; it warns
  if the queue is still registered.

## Queue locks and limits

**Queue and tag set locks**

- `update_nr_hwq_lock` takers, complete for this tree:

| Taker | Mode |
|---|---|
| `blk_mq_update_nr_hw_queues()` | write, blocking, then `tag_list_lock` |
| `disable_elv_switch()`, from `del_gendisk()` | write, blocking |
| `elv_iosched_store()` | write, `down_write_trylock()` |
| `queue_requests_store()` | write, `down_write_trylock()` |
| `add_disk_fwnode()` around `__add_disk()` | read, blocking, blk-mq only |
| `del_gendisk()` around `__del_gendisk()` | read, blocking, blk-mq only |

- `update_nr_hwq_lock` held for write: lets `queue_requests_store()` and
  `blk_mq_elv_switch_none()` read `q->elevator` without `elevator_lock`.
- `elevator_change()`: only asserts `update_nr_hwq_lock` with
  `lockdep_assert_held()`, so either mode passes; `elevator_set_default()`
  and `elevator_set_none()` reach it under the read side from
  `blk_register_queue()` and `blk_unregister_queue()`.
- `sysfs_lock`: not taken by `queue_attr_show()` or `queue_attr_store()`.
  It covers `blk_register_queue()` from after `blk_mq_sysfs_register()` to
  the uevents, the clear of `QUEUE_FLAG_REGISTERED`, and independent access
  ranges (asserted in `block/blk-ia-ranges.c`).
- `tag_list_lock`: also held around hctx kobject add and delete in
  `blk_mq_sysfs_register()` and `blk_mq_sysfs_unregister()`.
- `elevator_lock`: `wbt_lat_usec` is not under it, whatever the comment in
  `struct request_queue` says; `queue_wb_lat_show()` and `wbt_set_lat()`
  take `rqos_state_mutex` of `struct gendisk`.
- `elevator_lock`: also covers `async_depth`.
- `queue_lock`: does not cover `queue_flags`; `blk_queue_flag_set()` is a bare
  `set_bit()`. It covers `quiesce_depth`, `rpm_status`, `icq_list` and blkg
  creation.
- `requeue_lock`: covers `requeue_list` and `flush_list`.
- `limits_lock`: also held by `queue_attr_show()` around `->show_limit`, and
  by `queue_ra_show()` and `queue_ra_store()` for `read_ahead_kb`.
- `tags_srcu` in `struct blk_mq_tag_set`: defers freeing of tags against tag
  iteration; `srcu` beside it is for `BLK_MQ_F_BLOCKING`.
- There is no sysfs_dir_lock field in `struct request_queue`.

**Tag set lock in sysfs**

- In-tree stores that take `update_nr_hwq_lock`: `elv_iosched_store()` in
  `block/elevator.c` and `queue_requests_store()` in `block/blk-sysfs.c`.
- Both use `down_write_trylock()` and return `-EBUSY` when it fails;
  `queue_attr_store()` passes that to user space unchanged.
- Write mode in `elv_iosched_store()`: serialises both stages of
  `elevator_change()`, the switch and `elevator_change_done()`.
- Holder that waits for the store: `del_gendisk()` keeps the read side across
  `__del_gendisk()`, which reaches `kobject_del(&disk->queue_kobj)` through
  `blk_unregister_queue()`.
- `q->tag_set`: dereferenced with no check and no reference; safe because both
  attributes are in `blk_mq_queue_attrs`, which `blk_mq_queue_attr_visible()`
  hides for bio-based queues.
- Allocation goes between the trylock and the freeze:
  `queue_requests_store()` calls `blk_mq_alloc_sched_tags()` there.
- **Unsafe usage**: a blocking `down_read()` or `down_write()` on
  `update_nr_hwq_lock` in the store function of a queue attribute.
  - Unsafe: the store holds a kernfs active reference on its attribute while
    `del_gendisk()` holds the lock and waits in `kobject_del()` for that
    reference.
  - Safe: `down_write_trylock()` and `-EBUSY`, as `elv_iosched_store()` and
    `queue_requests_store()` do.
  - Safe: a blocking acquisition outside any sysfs callback of the disk and
    its queue, as `add_disk_fwnode()` and `blk_mq_update_nr_hw_queues()` do;
    `__del_gendisk()` removes those attributes under the read side.

**Lock order around a freeze**

- `queue_attr_store()` with `->store`: holds no lock and no freeze.
- `queue_attr_store()` with `->store_limit`: holds `limits_lock` only, queue
  not frozen; it never takes `sysfs_lock`.
- `tag_list_lock`: before the freeze, see `blk_mq_update_tag_set_shared()` and
  `__blk_mq_update_nr_hw_queues()`.
- `sysfs_lock`: before the freeze; `blk_register_queue()` holds it across
  `elevator_set_default()`.
- `elevator_lock`: show functions take it with no freeze, for example
  `queue_requests_show()` and `blk_mq_hw_sysfs_show()`.
- `rq_qos_mutex`: no single order. `rq_qos_add()` and `rq_qos_del()` assert it
  and freeze inside; `ioc_qos_write()` drops it, freezes, then retakes it.
- `debugfs_mutex`: `debugfs_create_files()` asserts that `elevator_lock` and
  `rq_qos_mutex` are not held; `wbt_set_lat()` and `elevator_change_done()`
  register debugfs entries after the unfreeze.
- `rqos_state_mutex` of `struct gendisk`: taken under the freeze in
  `wbt_set_lat()`.
- `queue_ra_store()`: takes `limits_lock`, does not freeze.
- `queue_wb_lat_store()`: calls `wbt_set_lat()`, takes no `elevator_lock`.
- Lockdep maps: fields `io_lockdep_map` and `q_lockdep_map`; a report prints
  them as "&q->q_usage_counter(io)" and "&q->q_usage_counter(queue)".
- `blk_freeze_acquire_lock()`: exclusive acquire with trylock set, so lockdep
  records no dependency from locks already held to the freeze, only from the
  freeze to locks taken under it.
- Opposite edge: comes from `bio_queue_enter()`, `__bio_queue_enter()` and
  `blk_queue_enter()`, which do a non-trylock read acquire and release.
- Lockdep therefore reports a lock that is taken under a freeze and also held
  while entering the queue; it does not check a lock held when the freeze
  starts.
- `mq_freeze_disk_dead`: set by `blk_freeze_set_owner()` when `q->disk` is
  NULL, `GD_DEAD` is set, or the queue is not registered; `io_lockdep_map` is
  then skipped, so a freeze before `add_disk()` is not modelled on it.
- Modelled freezes: only the first freeze (`mq_freeze_depth` 0) with an owner
  task; released when that task's `mq_freeze_owner_depth` reaches 0.
- Not modelled: nested freezes, `blk_freeze_queue_start_non_owner()` and
  `blk_mq_unfreeze_queue_non_owner()`.

**Updating queue limits**

- `queue_limits_commit_update()`: never freezes and does not check for a
  freeze; it only asserts `limits_lock`.
- "No outstanding I/O by other means", in-tree examples: `loop_configure()`
  (device not bound yet), `__loop_clr_fd()` (final release), `nbd_set_size()`
  (zero capacity, no write cache).
- `queue_limits_commit_update_frozen()`: no requirement on outstanding I/O; it
  calls `blk_mq_freeze_queue()` itself around the commit.
- `queue_limits_commit_update_frozen()`: works on bio-based queues too;
  `queue_attr_store()` uses it for every queue.
- Freezes nest by `mq_freeze_depth`, so a second freeze by itself does not
  hang.
- I/O between start and commit: allowed; `sd_revalidate_disk()` issues
  commands to the same queue while it holds `limits_lock`.
- **Unsafe usage**: `queue_limits_start_update()`, `queue_limits_set()` or
  `mutex_lock(&q->limits_lock)` on a queue the caller has frozen.
  - Unsafe: a holder of `limits_lock` such as `sd_revalidate_disk()` blocks in
    `blk_queue_enter()` until the unfreeze, and the freezer blocks on
    `limits_lock`.
  - Safe: start, then `queue_limits_commit_update_frozen()`, as
    `queue_attr_store()` does.
  - Safe: start, `blk_mq_freeze_queue()`, `queue_limits_commit_update()`,
    `blk_mq_unfreeze_queue()`, as `nvme_update_ns_info_generic()` does.
  - Safe: giving up under that freeze with `queue_limits_cancel_update()`
    before the unfreeze, as `disk_update_zone_resources()` does.

**Validation of queue limits**

- Return value: `-EINVAL` on every failure path of `blk_validate_limits()`,
  `blk_validate_integrity_limits()`, `blk_validate_zoned_limits()` and the
  crypto check in `queue_limits_commit_update()`.
- Caller's copy after a failed commit: partly rewritten with defaults and
  caps, up to the check that failed.
- `virt_boundary_mask` together with `max_segment_size`: accepted; with a
  virt boundary an unset `max_segment_size` becomes `UINT_MAX` and its minimum
  is not checked.
- Minimum for `max_user_sectors`, `seg_boundary_mask` and `max_segment_size`:
  `BLK_MIN_SEGMENT_SIZE` (4096) in `block/blk.h`, not the page size.
- `max_hw_sectors`: the one limit compared with `PAGE_SECTORS`; also rejected
  when smaller than one logical block.
- Fixed up, not rejected: `physical_block_size` below logical, `io_min` below
  physical, `BLK_FEAT_FUA` without `BLK_FEAT_WRITE_CACHE`,
  `discard_granularity`, atomic write limits.
- `physical_block_size`: rejected only when it is at least the logical size
  and not a power of two.
- `max_hw_wzeroes_unmap_sectors`: rejected when non-zero and different from
  `max_write_zeroes_sectors`.
- Crypto check, under `CONFIG_BLK_INLINE_ENCRYPTION`: rejects
  `q->crypto_profile` together with a non-zero `lim->integrity.tag_size`.
- `WARN_ON_ONCE()` on failure: the checks of `max_hw_sectors`,
  `seg_boundary_mask`, `max_segment_size`, `dma_alignment` and of zone limits
  on a non-zoned queue. The block size and integrity checks only `pr_warn()`;
  the `max_user_sectors` and `max_hw_wzeroes_unmap_sectors` checks are silent.

## Schedulers

**Switching schedulers**

- `elv_iosched_store()`: takes `set->update_nr_hwq_lock` for write, with
  `down_write_trylock()`, and returns `-EBUSY` when the lock is contended.
- Comments in `block/blk-sysfs.c`, `block/blk-mq.c` and
  `block/blk-mq-sched.c` say the switch holds that lock for read;
  `elv_iosched_store()` does not.
- Pre-freeze allocation: there is no elv_alloc_et() here;
  `blk_mq_alloc_sched_res()` in `block/blk-mq-sched.c` fills the `res` member
  (`struct elevator_resources`) of `struct elv_change_ctx`.
- `res.et`: scheduler tags from `blk_mq_alloc_sched_tags()`;
  `struct elv_change_ctx` has no `et` member of its own.
- `res.data`: private data from the `alloc_sched_data` op, through
  `blk_mq_alloc_sched_data()`; `NULL` when the type has no such op.
- `alloc_sched_data`: only `block/kyber-iosched.c` sets it.
- Still allocated inside the freeze, with `GFP_KERNEL` under the
  `memalloc_noio_save()` of `blk_mq_freeze_queue()`: the
  `struct elevator_queue` in `elevator_alloc()`, private data in
  `dd_init_sched()` and `bfq_init_queue()`, per-hctx data in
  `kyber_init_hctx()`.
- Unused resources: `elevator_change()` frees them with
  `blk_mq_free_sched_res()` when `ctx->new` is `NULL`; that covers the
  same-name switch too.
- `elevator_exit()`: while frozen, also takes `sysfs_lock` of the old
  `struct elevator_queue` around `blk_mq_exit_sched()`, which sets
  `ELEVATOR_FLAG_DYING`.
- Failure inside `blk_mq_init_sched()` (`elevator_alloc()`, `init_sched` or
  `init_hctx`): `q->elevator` is `NULL`, the old scheduler is not restored.
- Failure before `elevator_exit()`: the old scheduler stays. For example,
  `blk_mq_alloc_sched_res()` fails before the freeze, or
  `elevator_find_get()` in `elevator_switch()` finds no such name and returns
  `-EINVAL`.

**Switch steps after unfreeze**

- Scheduler debugfs: registered and removed after the unfreeze, not in
  `blk_mq_init_sched()`. `elv_register_queue()` calls
  `blk_mq_sched_reg_debugfs()`, `elv_unregister_queue()` calls
  `blk_mq_sched_unreg_debugfs()`; each takes `q->debugfs_mutex` itself.
- `elv_register_queue()`: skips debugfs registration when `kobject_add()`
  failed.
- wbt: `elevator_change_done()` has no wbt step, and there is no
  ELEVATOR_FLAG_ENABLE_WBT_ON_EXIT in this tree. The only call of
  `wbt_enable_default()` in a switch is in `bfq_exit_queue()`, inside a freeze
  under `q->elevator_lock`.
- Old scheduler's resources: freed with `blk_mq_free_sched_res()`, which frees
  the tags and calls `free_sched_data` when the type has that op.
- `ctx->old`: `elevator_change_done()` is the only code that unregisters it,
  frees its scheduler tags and puts its kobject; `elevator_exit()` does none
  of these.
- `q->elevator_lock`: released before the unfreeze; not held when
  `elevator_change_done()` is called.
- `q->sysfs_lock`: not taken by `elevator_change_done()` or its callees.
- Locks the caller holds across both stages:

  | Path | `set->update_nr_hwq_lock` | Also held |
  |---|---|---|
  | `elv_iosched_store()` | write | none |
  | `blk_register_queue()` to `elevator_set_default()` | read, in `add_disk_fwnode()` | `q->sysfs_lock` |
  | `blk_unregister_queue()` to `elevator_set_none()` | read, in `del_gendisk()` or `add_disk_fwnode()` | none |
  | `blk_mq_elv_switch_none()` to `elevator_set_none()` | write | `set->tag_list_lock` |
  | `elv_update_nr_hw_queues()`, which calls `elevator_switch()` itself | write | `set->tag_list_lock` |

- From `elv_iosched_store()`: the write lock keeps `queue_requests_store()`,
  `blk_mq_update_nr_hw_queues()`, `add_disk_fwnode()` and `del_gendisk()` on
  the same tag set out until `elevator_change_done()` has returned.

**Depth update callback**

- At initialisation the core does not call `depth_updated`. Each scheduler's
  `init_sched` calls its own function by name: `dd_init_sched()`,
  `kyber_init_sched()`, `bfq_init_queue()`.
- The comment above `dd_depth_updated()` names `blk_mq_init_sched()` as a
  caller; `blk_mq_init_sched()` has no such call.
- Later callers through the op: `blk_mq_update_nr_requests()` in
  `block/blk-mq.c` and `queue_async_depth_store()` in `block/blk-sysfs.c`.
  Both skip a `NULL` op.
- `q->async_depth`: a member of `struct request_queue`. All three callbacks
  read it; none reads `q->nr_requests`.
- What is written when the callback runs:

  | Caller | `q->nr_requests` | `q->async_depth` | Queue state |
  |---|---|---|---|
  | the scheduler's `init_sched` | set by `blk_mq_init_sched()` from the `struct elevator_tags` | not written by the core; set only if `init_sched` wrote it before the call | frozen, quiesced, `q->elevator_lock` |
  | `blk_mq_update_nr_requests()` | new value | rescaled by new over old `nr_requests`, at least 1, before `q->nr_requests` is written | frozen, quiesced, `q->elevator_lock`, `update_nr_hwq_lock` for write |
  | `queue_async_depth_store()` | unchanged | `min()` of `q->nr_requests` and the stored value | frozen, `q->elevator_lock`; not quiesced, `update_nr_hwq_lock` not taken |

- `queue_async_depth_store()`: returns `-EINVAL` when `q->elevator` is `NULL`.
- `q->elevator`: `blk_mq_init_sched()` never assigns it on success;
  `init_sched` must set `q->elevator = eq`, and `elevator_switch()` reads it
  back into `ctx->new`.
- `eq->elevator_data`: already set by `elevator_alloc()` from `res->data` for a
  type with `alloc_sched_data`; `kyber_init_sched()` does not write it. Other
  types set it in `init_sched`.
- **Unsafe usage**: an `init_sched` that calls its depth function before it
  writes `q->async_depth`.
  - Unsafe: the function computes its limits from the value left from before
    the switch; the core does not write `q->async_depth` before `init_sched`.
  - Safe: write `q->async_depth`, then call, as `dd_init_sched()` and
    `kyber_init_sched()` do; `dd_depth_updated()` passes `q->async_depth` to
    `blk_mq_set_min_shallow_depth()`.

## Requests and dispatch

**Request state and timeouts**

- `rq->state`: every state change is a plain `WRITE_ONCE()`; there is no
  `cmpxchg()` on it and no blk_mq_change_rq_state() or blk_mq_set_rq_state()
  in this tree.
- `blk_mq_complete_request()`: returns void and sets `MQ_RQ_COMPLETE`
  unconditionally; it cannot fail or detect an earlier completion.
- `blk_mq_end_request()` and `__blk_mq_end_request()`: never read `rq->state`,
  so a second call is not rejected.
- `MQ_RQ_COMPLETE` writers: `blk_mq_complete_request_remote()`,
  `blk_mq_set_request_complete()`, `blk_mq_complete_request_direct()`.
- A request ended with `blk_mq_end_request()` without a complete call goes
  from `MQ_RQ_IN_FLIGHT` straight to `MQ_RQ_IDLE`;
  `blk_mq_request_completed()` is never true for it.
- `rq->ref`: an `atomic_t`, not a `refcount_t`; helpers are in `block/blk.h`
  and so are not usable from drivers.
- `blk_mq_find_and_get_req()`: takes no lock and does not use `tags->lock`;
  the busy iterators hold `srcu_read_lock()` on `tags_srcu` of
  `struct blk_mq_tag_set`.
- `blk_mq_free_request()`: writes `MQ_RQ_IDLE` before it drops its reference,
  so a timeout handler can see `MQ_RQ_IDLE` or `MQ_RQ_COMPLETE` on a request
  whose tag is released only when `bt_iter()` puts the last reference.
- `blk_mq_put_rq_ref()` on a flush request: calls `rq->end_io`
  (`flush_end_io()` in `block/blk-flush.c`) instead of
  `__blk_mq_free_request()`.
- Handler's reference: `bt_iter()` drops it as soon as the callback returns;
  work the handler defers has no reference of its own.
- `RQF_TIMED_OUT`: set by `blk_mq_rq_timed_out()` before the handler runs;
  while set, `blk_mq_req_expired()` returns false. After `BLK_EH_DONE` the
  core never times that request out again unless `blk_add_timer()` or
  `__blk_mq_requeue_request()` clears the flag.
- `timeout` context: the only caller is `blk_mq_rq_timed_out()`, from
  `q->timeout_work` on kblockd, inside the `tags_srcu` read section; the
  handler may sleep.
- **Potentially unsafe usage**: completing or ending the request from the
  `timeout` handler.
  - Unsafe: while the driver's normal completion path can still reach the same
    request; both sides run `blk_mq_free_request()`, which drops `rq->ref`
    twice.
  - Safe: reap pending completions with the interrupt disabled, then return
    `BLK_EH_DONE` without completing if the state is no longer
    `MQ_RQ_IN_FLIGHT`, as `nvme_timeout()` does with `nvme_poll_irqdisable()`
    on a queue that is not polled.
  - Safe: mark completion and test `blk_mq_request_completed()` under the same
    driver lock, as `null_timeout_rq()` and `null_poll()` do with
    `nq->poll_lock` on a `HCTX_TYPE_POLL` queue.

**Driver dispatch contract**

- `BLK_STS_OK`: means the driver has taken or already disposed of the request;
  the core checks nothing. In-tree `queue_rq` returns it after ending the
  request (`z2_queue_rq()`), completing it unstarted
  (`nvme_fail_nonready_command()` through `nvme_host_path_error()`), or
  requeueing it with `blk_mq_requeue_request()` (`null_queue_rq()`).
- `blk_mq_start_request()`: the only place that stores a request in
  `tags->rqs[]` and the only writer of `MQ_RQ_IN_FLIGHT`; a request held
  without it has no timeout and is skipped by `blk_mq_tagset_busy_iter()`.
- Non-OK return after `blk_mq_start_request()`: allowed.
  `__blk_mq_requeue_request()` resets a started request to `MQ_RQ_IDLE` on a
  busy status, as `scsi_queue_rq()` relies on; `loop_queue_rq()` starts and
  then returns `BLK_STS_IOERR`.
- BLK_STS_ZONE_RESOURCE: not defined in this tree; there is no zone-busy list
  in `blk_mq_dispatch_rq_list()`.
- Rerun after a busy status in `blk_mq_dispatch_rq_list()` depends only on
  `BLK_MQ_S_SCHED_RESTART`, not on what is in flight:

| `BLK_MQ_S_SCHED_RESTART` | `BLK_STS_RESOURCE` | `BLK_STS_DEV_RESOURCE` |
|---|---|---|
| clear | `blk_mq_run_hw_queue(hctx, true)` at once | same |
| set | `blk_mq_delay_run_hw_queue()` after `BLK_MQ_RESOURCE_DELAY` | no run by the core |

- `BLK_MQ_S_SCHED_RESTART` is set by `__blk_mq_sched_dispatch_requests()` when
  it starts from a non-empty `hctx->dispatch`; `blk_mq_dispatch_rq_list()`
  does not set it for a driver status.
- `BLK_STS_DEV_RESOURCE` with the flag set: the core schedules no run; the
  flag is acted on by `blk_mq_sched_restart()`, called from
  `__blk_mq_free_request()` and `mq_flush_data_end_io()`.
- `blk_mq_mark_tag_wait()`: runs only when `blk_mq_get_driver_tag()` fails,
  not for a status from `queue_rq`.
- Driver tag on requeue: `blk_mq_put_driver_tag()` releases it only when the
  request also has a scheduler tag; with no elevator the request keeps
  `rq->tag`.
- Direct issue (`blk_mq_try_issue_directly()`, `blk_mq_issue_direct()`): both
  busy statuses get `blk_mq_request_bypass_insert()` and
  `blk_mq_run_hw_queue(hctx, false)`; no `BLK_MQ_S_SCHED_RESTART` test, no
  `BLK_MQ_RESOURCE_DELAY`.
- Budget (`get_budget`): once `queue_rq` is called, releasing that request's
  budget is the driver's job. On a non-OK return the driver must release it
  and make `get_rq_budget_token` return a negative value, because
  `blk_mq_release_budgets()` also walks the refused request and puts any
  token that is not negative; `scsi_queue_rq()` sets
  `cmd->budget_token = -1`.
- `bd->last` in `blk_mq_issue_direct()`: computed over the whole list passed
  in, which can span hardware queues; on each switch the previous queue gets
  `commit_rqs` even though every return was `BLK_STS_OK`.
- `commit_rqs` with nothing pending: `queued` counts every `BLK_STS_OK`,
  including requests the driver ended or requeued itself and requests
  `blk_mq_request_issue_directly()` inserted without calling `queue_rq`.

**Dispatch calling context**

- Read-side section: `__blk_mq_run_dispatch_ops()` in `block/blk-mq.h`; the
  SRCU is `srcu` of `struct blk_mq_tag_set`. There is no hctx_lock() and no
  per-hctx SRCU in this tree.
- `__blk_mq_run_dispatch_ops()` with `BLK_MQ_F_BLOCKING`: calls
  `might_sleep_if(check_sleep)`; `blk_mq_run_dispatch_ops()` passes true, so
  direct issue on a blocking queue asserts a sleepable caller.
- Direct issue: adds nothing beyond the RCU or SRCU section; it does not
  disable preemption or interrupts.
- `blk_mq_run_hw_queue()` with `async` false: dispatches inline only when the
  current CPU is in `hctx->cpumask`; otherwise it goes to kblockd through
  `blk_mq_delay_run_hw_queue()`.
- kblockd run: `blk_mq_hctx_next_cpu()` returns `WORK_CPU_UNBOUND` when
  `nr_hw_queues` is 1, the mask is empty, or no mapped CPU is online; then
  `queue_rq` can run on a CPU outside `hctx->cpumask`.
- Plug flush from `schedule()`: `blk_mq_flush_plug_list()` with
  `from_schedule` true skips direct issue and makes every run async;
  `queue_rq` is not called inline there, with or without `BLK_MQ_F_BLOCKING`.
- Atomic callers on a blocking queue: `blk_mq_run_hw_queue()` does not switch
  to async for them; it only has `might_sleep_if()`. The caller must
  pass `async` true, as `blk_mq_start_hw_queue()` and
  `blk_execute_rq_nowait()` do by passing `hctx->flags & BLK_MQ_F_BLOCKING`.
- Interrupt context: the only `in_interrupt()` test is
  `WARN_ON_ONCE(!async && in_interrupt())` in `blk_mq_run_hw_queue()`; the
  direct-issue paths have none of their own.
- NVMe TCP: the flag comes from `NVME_F_BLOCKING` in the controller ops,
  applied in `nvme_alloc_io_tag_set()` and `nvme_alloc_admin_tag_set()`, not
  in `nvme_tcp_queue_rq()`.
- `commit_rqs` and `queue_rqs`: called inside the same section as `queue_rq`,
  so the same sleeping rule applies.

## Model gaps

### Other mistakes models make

- Models do not know `blk_crypto_submit_bio()`. `submit_bio_noacct()` ends a
  bio that has a crypt context with `BLK_STS_NOTSUPP` unless
  `blk_crypto_supported()`; the fallback runs only from
  `__blk_crypto_submit_bio()` in `block/blk-crypto.c`.
- Models take a split to fail only for `REQ_NOWAIT` or `REQ_ATOMIC`.
  `bio_split_io_at()` in `block/blk-merge.c` also returns `-EINVAL` for a
  bvec not aligned to `lim->dma_alignment` or when no block-aligned split
  exists, and `blk_mq_submit_bio()` fails a bio that `bio_unaligned()`
  rejects.
- Models take `blk_mq_find_and_get_req()` to run under `tags->lock`.
  `tags->lock` is taken only around the `active_queues` update, in
  `__blk_mq_tag_busy()` and `__blk_mq_tag_idle()`.
- Models take `elevator_change_done()` to re-enable wbt through
  ELEVATOR_FLAG_ENABLE_WBT_ON_EXIT. `wbt_enable_default()` only changes
  state, and `wbt_init_enable_default()`, called from
  `blk_register_queue()`, creates the policy. BFQ uses
  `QUEUE_FLAG_DISABLE_WBT_DEF`.
- Models name blk_mq_alloc_sched_tags_batch() or only
  `blk_mq_alloc_sched_tags()` as what is allocated before the freeze.
  `elevator_alloc()` takes the preallocated `struct elevator_resources` as
  its third argument.
- Models call the `blk_get_queue()` reference a kobject refcount. It is
  `refcount_t refs`, `blk_get_queue()` returns false on a dying queue, and
  the "queue" kobject is `queue_kobj` in `struct gendisk`.
- Models do not know `bio_await()`, declared in `include/linux/bio.h` and
  defined in `block/bio.c`.
- Models name QUEUE_FLAG_SKIP_TAGSET_QUIESCE. The test is
  `blk_queue_skip_tagset_quiesce()` in `include/linux/blkdev.h`.
