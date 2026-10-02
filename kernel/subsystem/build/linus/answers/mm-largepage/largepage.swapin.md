- There is no alloc_swap_folio(), swapin_folio(), add_to_swap_cache(),
  __read_swap_cache_async() or SWAP_HAS_CACHE here. A cached slot is a folio
  entry in the swap table, tested with `swp_tb_is_folio()`.
- `swap_cache_alloc_folio()`: takes an `orders` mask, not one order. It
  returns a new folio or `ERR_PTR()`; never NULL, never an existing folio.
- New folio on return: locked, in the swap cache, memcg-charged, passed to
  `folio_add_lru()`, not uptodate. `folio->swap` is `targ_entry` rounded down
  to the folio size.
- Fallback is inside `swap_cache_alloc_folio()`: on `-EBUSY` or `-ENOMEM` it
  tries the next lower order set in `orders`.
- Order 0 is tried only if `BIT(0)` is in `orders`. `do_swap_page()` passes
  it; `shmem_swap_alloc_folio()` passes one order and retries with 0 itself.
- Errors from `swap_cache_alloc_folio()`:

| Error | Cause | Fallback |
|---|---|---|
| `-EEXIST` | target slot already has a folio | none, returned at once |
| `-ENOENT` | target slot has count 0, or cluster has no table | none |
| `-EBUSY` | another slot in the range fails the check | next order |
| `-ENOMEM` | allocation, memcg charge or `folio_memcg_alloc_deferred()` failed | next order |
| `-EINVAL` | `orders` is 0, or its highest order exceeds `SWAPFILE_CLUSTER` pages | none, with a warning |

- `__swap_cache_add_check()`: runs under `ci->lock`, before the allocation and
  again before the insert. Every slot needs a count, no folio, and the same
  zeromap bit as the target; the second run also needs the same memcg id.
- `swap_zeromap_batch()`: static in `mm/page_io.c`; callers of
  `swap_cache_alloc_folio()` do not use it.
- Memcg charge: made after the insert. On failure `__swap_cache_alloc()`
  removes the folio, restores the shadow and returns `-ENOMEM`.
- Page tables: `swap_cache_alloc_folio()` checks the swap table only.
  `thp_swapin_suitable_orders()` filters `orders` by the PTEs beforehand.
- `SWP_SYNCHRONOUS_IO`: there is no swap cache bypass. The flag selects
  `swapin_sync()`, which skips readahead and allows large orders.
  `swap_cache_read_folio()` always passes `BIT(0)`.
- `swapin_sync()`: returns `ERR_PTR()` on failure, and NULL without
  `CONFIG_SWAP`. `swapin_readahead()` returns NULL on failure.
- `swapin_sync()` result: may be an older swap cache folio, unlocked and of
  any order. Take the size from the folio, as `shmem_swapin_folio()` does
  with `shmem_split_large_entry()`.
- After locking the folio: `folio_matches_swap_entry()` is required, as in
  `do_swap_page()` and `shmem_swapin_folio()`.
- Fresh large folio whose PTEs changed: `do_swap_page()` does not map part of
  it. It calls `swap_cache_del_folio()` and returns for a retry.
- Swap device: must be pinned across the call, for example with
  `get_swap_device()`; `__swap_offset_to_cluster()` has only a
  `VM_WARN_ON_ONCE()` for a device with no users.
- **Unsafe usage**: reading swap data into a folio that is not in the swap
  cache.
  - Safe: `swap_cache_alloc_folio()` then `swap_read_folio()`, as
    `swapin_sync()` does. `swap_read_folio()` takes the slot from
    `folio->swap`, and `zswap_load()` warns if the folio is not swap cache.
- **Unsafe usage**: a large order in `orders` once zswap has been enabled.
  `zswap_load()` warns, unlocks and leaves the folio not uptodate, which gives
  `VM_FAULT_SIGBUS` in `do_swap_page()`.
  - Safe: order 0 only when `!zswap_never_enabled()`, as
    `thp_swapin_suitable_orders()` and `shmem_swap_alloc_folio()` do.
- **Unsafe usage**: leaving a new folio from `swap_cache_alloc_folio()` in the
  swap cache without reading into it. `do_swap_page()` returns
  `VM_FAULT_SIGBUS` for a folio that is not uptodate.
  - Safe: `swap_cache_del_folio()`, `folio_unlock()`, `folio_put()`, as the
    error path of `zswap_writeback_entry()` does.
