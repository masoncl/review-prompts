- `folio_put_swap()`: never frees a slot or the folio; a cached slot whose
  count reaches 0 is freed when the folio leaves the swap cache.
- `swap_put_entries_direct()`: pins the device itself with
  `get_swap_device()`, range-checks against `si->max`, and splits a range
  that crosses clusters.
- `swap_dup_entry_direct()`: takes no device reference and does not check the
  offset; the caller's lock on the live swap PTE must provide both.
- `folio_dup_swap()` and `folio_put_swap()`: act on one cluster; `page ==
  NULL` means every slot of the folio.
- Count 0 to 1: reserved to `folio_dup_swap()`; `swap_dup_entry_direct()`
  only checks this with `VM_WARN_ON_ONCE()`, and `__swap_cluster_dup_entry()`
  accepts count 0 on a cached slot.
- **Potentially unsafe usage**: `swap_put_entries_direct()` without the page
  table lock.
  - Unsafe: while another task can still find the entry and drop the same
    reference; `__swap_cluster_put_entry()` only warns on count 0 and then
    writes the decremented value.
  - Safe: under the PTL of the PTE that holds the entry, as
    `zap_nonpresent_ptes()` in `mm/memory.c` does.
  - Safe: after the entry was removed from the shmem mapping under the xarray
    lock, so the caller is the only owner, as `shmem_free_swap()` in
    `mm/shmem.c` does.
