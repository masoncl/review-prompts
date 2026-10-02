| Job | Function | Caller must hold |
|---|---|---|
| look up | `swap_cache_get_folio()` | device stabilised: `get_swap_device()`, a locked swap-cache folio, or the lock over what holds the entry (PTL) |
| add at swap-out | `folio_alloc_swap()` | folio locked and uptodate; it calls `__swap_cache_add_folio()` under the cluster lock |
| add at swap-in | `swap_cache_alloc_folio()` | device stabilised; allocates the folio, returns it locked and cached |
| delete | `swap_cache_del_folio()` | folio locked, in swap cache, not under writeback |
| delete, locked | `__swap_cache_del_folio()` | the same, plus the cluster lock |
| replace | `__swap_cache_replace_folio()` | both folios locked, cluster lock |

- swap_cache_add_folio(): not in this tree; `__swap_cache_add_folio()` has
  one caller, `__swap_cluster_alloc_entries()` in `mm/swapfile.c`.
- Lookup without a stabilised device: `__swap_type_to_info()` in `mm/swap.h`
  warns when `users` is zero.
- `__swap_cache_del_folio()`: leaves the folio's cache references to the
  caller; `swap_cache_del_folio()` drops them itself, `folio_nr_pages()` of
  them.
- `__swap_cache_del_folio()`: writes shadow format to every slot, then frees
  the slots whose count is 0.
- `__swap_cache_replace_folio()`: changes only the table; the caller sets
  `new->swap` and `PG_swapcache` on the new folio first and moves the
  references, as `shmem_replace_folio()` does.
- **Potentially unsafe usage**: `swap_cache_del_folio()` on a dirty folio.
  - Unsafe: when a slot still has a count; the slot stays in use with stale
    data on the device.
  - Safe: when every count is 0, which `folio_free_swap()` tests first.
