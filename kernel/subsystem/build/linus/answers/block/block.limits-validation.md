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
