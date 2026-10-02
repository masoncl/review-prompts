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
