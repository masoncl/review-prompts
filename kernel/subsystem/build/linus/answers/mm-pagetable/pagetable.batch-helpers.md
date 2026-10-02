- There is no clear_not_present_full_ptes() here; `clear_nonpresent_ptes()` in
  `include/linux/pgtable.h` does that, takes no `full` argument and loops over
  `pte_clear()`.
- `ptep_get_and_clear_full()` and `ptep_test_and_clear_young()`: single-PTE
  operations; the ranged forms are `get_and_clear_full_ptes()` and
  `test_and_clear_young_ptes()`.

| Helper | Bits that differ across the run | Requires of the run |
|---|---|---|
| `clear_full_ptes()`, `clear_ptes()` | all discarded; return `void` | present, one folio |
| `clear_flush_young_ptes()` | kept per entry; returns `bool`, true if any entry was young | present, one folio |
| `test_and_clear_young_ptes()` | kept per entry; returns `bool`, true if any entry was young; no TLB flush | present, one folio |
| `clear_young_dirty_ptes()` | kept per entry, apart from the bits the `cydp_t` flags clear | present, one folio |
| `modify_prot_start_ptes()` | the generic form clears each entry; an arch override may not, for example Xen PV leaves it present; returns the first with young and dirty ORed in | all bits but young and dirty identical |
| `modify_prot_commit_ptes()` | writes one value, PFN advanced per entry | entries that the start call was run on |
| `clear_nonpresent_ptes()` | all discarded | all not present; no folio relation |

- `modify_prot_start_ptes()`: the stricter requirement comes from the commit
  writing one value; `change_pte_range()` in `mm/mprotect.c` meets it by
  batching with `FPB_RESPECT_SOFT_DIRTY | FPB_RESPECT_WRITE`.
- `set_ptes()` with `nr` > 1: every entry must be not present before the call
  and present after it; `contpte_set_ptes()` in `arch/arm64/mm/contpte.c`
  relies on this and does not unfold or invalidate first.
- `set_ptes()` with `nr` == 1 (`set_pte_at()`): either state is allowed before
  and after.
