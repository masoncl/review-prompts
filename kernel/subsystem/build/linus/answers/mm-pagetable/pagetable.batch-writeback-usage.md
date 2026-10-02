- `folio_unmap_pte_batch()` in `mm/rmap.c`: passes
  `FPB_RESPECT_WRITE | FPB_RESPECT_SOFT_DIRTY`, not zero flags.
- `folio_unmap_pte_batch()`: returns 1 without batching for anon swapbacked
  folios, `TTU_HWPOISON`, small folios and `pte_unused()`; lazyfree and file
  folios are batched.
- `try_to_unmap_one()`: writes the run back with `set_ptes()` when
  `ttu_anon_folio()` fails; the value is the `get_and_clear_ptes()` result, so
  young and dirty spread over the run, while write and soft-dirty are uniform
  by the flags.
- `copy_present_ptes()` in `mm/memory.c`: passes `FPB_MERGE_WRITE`, plus
  `FPB_RESPECT_DIRTY` unless `VM_SHARED`, plus `FPB_RESPECT_SOFT_DIRTY` when
  `vma_soft_dirty_enabled()`; it never passes `FPB_RESPECT_WRITE`.
- `__copy_present_ptes()`, how each ignored bit is handled:
  - write, COW mapping: `wrprotect_ptes()` on the source run and
    `pte_wrprotect()` on the child value when the merged value is writable.
  - write, other mappings: the child run is written with the merged write bit.
  - dirty: uniform by flag in a private mapping; `pte_mkclean()` in a shared
    one.
  - young: `pte_mkold()` on the child value; the source keeps its own.
- `move_ptes()` in `mm/mremap.c`: batches through `mremap_folio_pte_batch()`,
  which returns 1 when `pte_batch_hint()` is 1, and otherwise passes
  `FPB_RESPECT_WRITE` for any large folio that `vm_normal_folio()` returns,
  anon or file.
- `move_ptes()`, ignored bits: young and dirty are ORed by
  `get_and_clear_ptes()`; `move_soft_dirty_pte()` sets soft-dirty on the value
  when `pgtable_supports_soft_dirty()`.
- No flags: `zap_present_ptes()` calls `folio_pte_batch()` and writes no
  present entry back; `zap_present_folio_ptes()` only clears, and may install
  `PTE_MARKER_UFFD_WP` markers from the userfaultfd bit, which is compared.
- Other callers of `folio_pte_batch()`: search for the name; each one only
  reads, clears, or uses a per-entry helper.
- **Unsafe usage**: writing one value over the run with `set_ptes()` or
  `modify_prot_commit_ptes()` after a batch that passed neither
  `FPB_RESPECT_WRITE` nor `FPB_MERGE_WRITE`.
  - Unsafe: the value carries the write bit of the first entry, so entries that
    were read-only become writable, or the reverse.
  - Safe: pass `FPB_RESPECT_WRITE`, as `mremap_folio_pte_batch()`,
    `folio_unmap_pte_batch()` and `change_pte_range()` do.
  - Safe: pass `FPB_MERGE_WRITE` and write-protect the whole run in a COW
    mapping, as `__copy_present_ptes()` does.
  - Safe: change entries only with a per-entry helper, as
    `madvise_free_pte_range()` does with `clear_young_dirty_ptes()`.
