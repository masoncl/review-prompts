- `move_ptes()`: clears the old entries with `get_and_clear_ptes()` only; it
  does not call `ptep_get_and_clear()`.
- `move_ptes()`: the earlier `ptep_get()` value is used for the none and
  present tests and for batching; the entry written is the one
  `get_and_clear_ptes()` returned.
- Large-folio batch: `get_and_clear_ptes()` ORs dirty and young over the
  batch, and `set_ptes()` writes that to every entry, so a clean entry can
  arrive dirty. Dirty is never dropped.
- `mremap_folio_pte_batch()`: batches with `FPB_RESPECT_WRITE` only, so
  entries that differ in dirty or soft-dirty share a batch.
- `force_flush` in `move_ptes()` and `move_huge_pmd()`: set for any present
  old entry, dirty or not.
- `move_soft_dirty_pmd()` in `mm/huge_memory.c`: under
  `pgtable_supports_soft_dirty()` it marks a present PMD and a migration
  entry (`pmd_is_migration_entry()`); other non-present PMDs are left as
  they are.
- `move_present_ptes()` in `mm/userfaultfd.c`: builds a new entry with
  `folio_mk_pte()`, so it sets soft-dirty under
  `pgtable_supports_soft_dirty()` and copies dirty from the source with
  `pte_dirty()`.
