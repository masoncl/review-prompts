- `finish_fault()`, `nr_pages` > 1 and the range not empty under the PTL: sets
  `needs_fallback`, drops the PTL, jumps back to `fallback:` and maps only the
  faulting page.
- `finish_fault()` returns `VM_FAULT_NOPAGE` only when `vmf_pte_changed()` is
  true for the faulting entry itself, or `pte_offset_map_lock()` returns NULL.
- `finish_fault()` maps the whole folio for any mapping, not only shmem, when
  all of these hold:
  - `userfaultfd_armed()` is false;
  - the folio fits inside the VMA and inside one page table;
  - the mapping is shmem, or the folio does not extend past `i_size`
    (`file_end < folio_next_index(folio)` sets `needs_fallback`);
  - every entry of the range is none under the PTL.
- `pte_range_none()`: static in `mm/memory.c`; reads with
  `ptep_get_lockless()`, which is what allows the call under `pte_offset_map()`
  without the PTL.
- `alloc_anon_folio()`: `pte_offset_map()` returning NULL gives
  `ERR_PTR(-EAGAIN)`, and `do_anonymous_page()` then returns 0.
- `do_anonymous_page()`: rechecks `folio_nr_pages(folio)` entries of the folio
  actually allocated, which can be a lower order than the first order that
  passed the unlocked check.
- `do_anonymous_page()`: tests `userfaultfd_missing()` under the PTL, after
  the recheck, and drops the folio before `handle_userfault()`.
- **Unsafe usage**: `set_ptes()` with `nr` > 1 over a range whose emptiness was
  checked only by an unlocked `pte_range_none()`.
  - Unsafe: `set_ptes()` with `nr` > 1 needs every entry not present;
    `contpte_set_ptes()` in `arch/arm64/mm/contpte.c` relies on it and does
    not unfold or invalidate first.
  - Safe: retake the table with `pte_offset_map_lock()`, repeat
    `pte_range_none()` over the folio's aligned range, and on failure drop the
    folio and return 0, as `do_anonymous_page()` does.
