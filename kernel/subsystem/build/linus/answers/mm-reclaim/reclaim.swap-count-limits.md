- Hibernation slots: start at count 1 in shadow format with no folio
  (`__swap_cluster_alloc_entries()` with a NULL folio); only slots allocated
  for a folio start at 0.
- Pin of a count-0 slot: lasts only while the folio stays locked; any task
  that locks the folio may free it, for example the allocator through
  `cluster_reclaim_range()`, whose callee `__try_to_reclaim_swap()` uses
  `folio_trylock()`.
- Count field: `SWP_TB_COUNT_BITS` wide, at most 4 bits, so
  `SWP_TB_COUNT_MAX` is at most 15.
- Overflow: there is no add_swap_count_continuation(), COUNT_CONTINUED or
  SWAP_MAP_MAX; a table count of `SWP_TB_COUNT_MAX` means the real count is in
  `extend_table` of `struct swap_cluster_info`, an `unsigned int` per slot.
- `extend_table`: allocated per cluster on demand by
  `swap_extend_table_alloc()`, freed by `swap_extend_table_try_free()` once
  every element is 0.
- `swp_tb_get_count()` and `__swap_count()`: return the saturated table
  value; of the count readers only `swp_swapcount()` reads `extend_table`.
- `swap_dup_entries_cluster()`: on overflow drops the cluster lock, tries a
  `GFP_ATOMIC` allocation, and on failure undoes the slots it raised and
  returns `-ENOMEM`.
- `folio_dup_swap()`: can therefore fail; `ttu_anon_swapbacked_folio()` in
  `mm/rmap.c` fails the unmap.
- Fork: `copy_nonpresent_pte()` turns any dup failure into `-EIO`;
  `copy_pte_range()` drops both PTLs, calls `swap_retry_table_alloc()` with
  `GFP_KERNEL`, and retries.
- **Potentially unsafe usage**: ignoring the return value of
  `folio_dup_swap()`.
  - Unsafe: when the slot's count can already be `SWP_TB_COUNT_MAX - 1`; the
    swap entry is installed without its reference.
  - Safe: right after `folio_alloc_swap()` with the folio still locked, where
    the count is 0 and `__swap_cluster_dup_entry()` cannot overflow, as
    `shmem_writeout()` does.
