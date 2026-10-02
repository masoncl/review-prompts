- `swap_cache_alloc_folio()` in `mm/swap_state.c`: returns a new folio or an
  `ERR_PTR()`, never NULL and never an existing folio. There is no
  new_page_allocated argument.

| Case | `__swap_cache_add_check()` | `swap_cache_alloc_folio()` |
|---|---|---|
| target slot holds a folio | `-EEXIST` | returned at once, at any order |
| target slot has count 0, or `ci->table` is NULL | `-ENOENT` | returned at once, at any order |
| another slot of the range is unsuitable | `-EBUSY` | retried at the next lower order in `orders` |
| folio allocation or memcg charge fails | 0 | `-ENOMEM`, retried like `-EBUSY` |
| `orders` is 0, or its highest order is above `SWAPFILE_CLUSTER` pages | not reached | `-EINVAL` |

- Target slot tests: run first, folio test before count test, so a cached
  target gives `-EEXIST` whatever the rest of the range holds.
- `-EEXIST`: handled by callers. `swap_cache_read_folio()` and
  `swapin_sync()` loop back to `swap_cache_get_folio()`;
  `zswap_writeback_entry()` returns the error.
- Unsuitable range: any slot of the aligned range that holds a folio, has
  count 0, has a zero flag different from the target slot's, or has a memcg
  id different from the target slot's.
- Memcg test: made only in the second check, where `memcg_id` is not NULL.
- Two checks in `__swap_cache_alloc()`, each under `ci->lock`: one before
  allocating, one just before insertion; a failure of the second frees the
  folio and returns the same codes.
- Not tested in `__swap_cache_add_check()`: zswap state. Callers pass no
  large order when `zswap_never_enabled()` is false; see
  `thp_swapin_suitable_orders()` and `shmem_swap_alloc_folio()`.
- `swap_zeromap_batch()`: static in `mm/page_io.c`; no caller of
  `swap_cache_alloc_folio()` pre-filters with it.
- Returned folio: locked, in the swap cache at the rounded-down entry,
  charged, passed to `folio_add_lru()`, not uptodate; the caller starts the
  read.
