- `fpb_t` in `mm/internal.h`: exactly five flags, `FPB_RESPECT_DIRTY`,
  `FPB_RESPECT_SOFT_DIRTY`, `FPB_RESPECT_WRITE`, `FPB_MERGE_WRITE` and
  `FPB_MERGE_YOUNG_DIRTY`.
- Young bit: ignored under every flag combination;
  `__pte_batch_clear_ignored()` ends with an unconditional `pte_mkold()`.
- `FPB_MERGE_WRITE` and `FPB_MERGE_YOUNG_DIRTY`: do not change what is
  compared; `__pte_batch_clear_ignored()` tests only `FPB_RESPECT_DIRTY`,
  `FPB_RESPECT_SOFT_DIRTY` and `FPB_RESPECT_WRITE`.
- `FPB_MERGE_YOUNG_DIRTY` with `FPB_RESPECT_DIRTY`: dirty must still match
  across the batch.
- Small folio: `folio_pte_batch_flags()` has no early return for it, only
  `VM_WARN_ON_FOLIO()`; callers make sure the folio is large first, as
  `mprotect_folio_pte_batch()` does with `folio_test_large()`.
- `ptentp` pointing into a page table: caught only by a `VM_WARN_ON()`, which
  is compiled out without `CONFIG_DEBUG_VM`; the merge flags write through
  `*ptentp`, so they would then modify the live entry.
- Userfaultfd bit (`pte_uffd()`): compared under every flag combination.
