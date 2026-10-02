- Return value: `min(nr, max_nr)` with `max_nr` already capped to the folio
  end, because `pte_batch_hint()` can step past `max_nr`.
- Folio end: capped by `folio_pte_batch_flags()` itself; the caller need not
  clamp to it.
- `max_nr` of 0: only a `VM_WARN_ON_FOLIO()` under `CONFIG_DEBUG_VM`; the
  function returns 0, so a loop that advances by the result does not advance.
- `max_nr` in `mm/memory.c`: computed in `copy_pte_range()` and
  `do_zap_pte_range()` as `(end - addr) / PAGE_SIZE`; `copy_present_ptes()`
  and `zap_present_ptes()` receive it as a parameter.
- `do_zap_pte_range()`: subtracts the leading none entries it skipped before
  it passes `max_nr` on.
- Run written into a second page table: `max_nr` must fit that table too;
  for `move_ptes()`, `get_extent()` in `mm/mremap.c` clamps the extent to the
  PMD of the old address and of the new one.
