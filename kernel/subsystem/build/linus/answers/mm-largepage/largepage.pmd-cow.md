- Huge zero PMD: `do_huge_zero_wp_pmd()` allocates a PMD-sized folio and maps
  it in place under its own MMU notifier range; the split runs only if it
  returns `VM_FAULT_FALLBACK`.
- `folio_trylock()` failure: no split; takes a reference, drops the PMD lock,
  sleeps in `folio_lock()`, retakes the PMD lock, rechecks `pmd_same()`, and
  returns 0 if the PMD changed.
- Count test, under the folio lock and the PMD lock:
  1. fall back if `folio_ref_count()` exceeds 1, plus `folio_nr_pages()` when
     the folio is in the swap cache
  2. `folio_free_swap()` if in the swap cache
  3. reuse only if `folio_ref_count()` is 1
- Unshare fault on a reusable folio: returns 0 with the PMD unchanged.
- `__split_huge_pmd()` on fallback: called with `freeze` false.
