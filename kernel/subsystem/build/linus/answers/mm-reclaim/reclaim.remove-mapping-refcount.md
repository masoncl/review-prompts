- Swap-cache path, in order under the cluster lock: `workingset_eviction()`,
  `__memcg1_swapout()`, `__swap_cache_del_folio()`, unlock; there is no
  put_swap_folio() and no __delete_from_swap_cache().
- `workingset_eviction()` must precede `__memcg1_swapout()`, which clears
  `folio->memcg_data` under `do_memsw_account()`; `lru_gen_eviction()` reads
  `folio_memcg()`.
- Swap slot without a shadow: not cleared; `__swap_cache_do_del_folio()`
  stores `shadow_to_swp_tb(NULL, flags)`, an empty shadow-format entry that
  keeps the old entry's flags field (`__swp_tb_get_flags()`: swap count and
  inline zero flag).
- Large swap-cache folio: every one of its slots gets the same shadow value.
- Slots whose swap count is zero: reset to NULL by
  `__swap_cluster_free_entries()` in the same call.
- Page-cache slot without a shadow: the folio's whole index range is set to
  NULL by one `xas_store()` in `page_cache_delete()`.
- `mapping->a_ops->free_folio()`: page-cache path only.
