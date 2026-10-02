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
