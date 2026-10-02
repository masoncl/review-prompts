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
