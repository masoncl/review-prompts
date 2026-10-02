- Names: there is no swap_shmem_alloc() here; `shmem_writeout()` raises the
  count with `folio_dup_swap(folio, NULL)` before
  `shmem_delete_from_page_cache()`.
- Stale check in `shmem_swapin_folio()`: `folio_matches_swap_entry()` and
  `shmem_confirm_swap()` are both tested after `folio_lock()`. The folio
  test alone does not show that the mapping still holds the entry.
- `shmem_confirm_swap()`: reads the slot under `rcu_read_lock()` only, not
  the `i_pages` lock.
- `shmem_add_to_page_cache()`: with `expected` set it walks every entry in
  the folio's range and requires consecutive swap values that cover it
  exactly; otherwise `-EEXIST`.
- Large entry value: the swap entry of its first page. For an index inside
  it, `shmem_swapin_folio()` adds `index - round_down(index, 1 << order)`
  to the offset before the swap cache lookup.
- After the folio is found: `shmem_swapin_folio()` rounds `swap` and
  `index` down to the folio size before the locked checks.
- `shmem_free_swap()`: uses `xas_load()` and `xas_store()` under
  `xas_lock_irq()`, not `xa_cmpxchg_irq()`, then
  `swap_put_entries_direct()`. It leaves a large entry in place, and
  returns 0, when the entry reaches outside the range it was given.
