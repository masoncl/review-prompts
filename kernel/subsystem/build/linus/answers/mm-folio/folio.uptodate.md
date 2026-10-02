- Flag update: one XOR that flips both bits, in every architecture's
  `xor_unlock_is_negative_byte()`; the generic
  `arch_xor_unlock_is_negative_byte()` in `include/asm-generic/bitops/lock.h`
  is `raw_atomic_long_fetch_xor_release()`, there is no two-step fallback.
- Error flag: this tree has no PG_error page flag; a failed read shows on the
  folio only as unlocked without `PG_uptodate`.
- Last completion of a partial read: either `iomap_finish_folio_read()` or
  the submitter in `iomap_read_end()` calls `folio_end_read()`, whichever
  brings `ifs->read_bytes_pending` to zero under `ifs->state_lock`.
- **Unsafe usage**: setting `PG_uptodate` on a folio whose read will be ended
  by `folio_end_read(folio, true)`; the XOR then clears the flag, and only
  `VM_BUG_ON_FOLIO()` in `folio_end_read()` checks for it.
  - Safe: leave the flag alone while the read is pending, as
    `iomap_set_range_uptodate()` does when `ifs->read_bytes_pending` is
    non-zero.
  - Safe: `folio_mark_uptodate()` then `folio_unlock()` when no
    `folio_end_read()` will follow, as `iomap_read_end()` unlocks when
    `ifs->read_bytes_pending` is already zero.
- **Potentially unsafe usage**: touching the folio after `folio_end_read()`.
  - Unsafe: in a completion handler for a folio taken with
    `readahead_folio()`, which drops the reference before the I/O; the lock
    was all that kept the folio in the cache.
  - Safe: when the caller holds its own reference, as `aio_setup_ring()` in
    `fs/aio.c` does from `__filemap_get_folio()`.
