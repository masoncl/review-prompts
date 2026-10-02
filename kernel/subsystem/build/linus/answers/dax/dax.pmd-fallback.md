- COW test in `dax_fault_check_fallback()`: `FAULT_FLAG_WRITE` set and
  `VM_SHARED` clear; `vmf->cow_page` is not read.
- Extent shorter than `PMD_SIZE`: tested with `iomap_length()` in the loop of
  `dax_iomap_pmd_fault()`, not in `dax_fault_iter()`.
- `dax_pmd_load_hole()`: falls back only when `mm_get_huge_zero_folio()`
  returns NULL; a PMD that is no longer none gives `VM_FAULT_NOPAGE` from
  `insert_pmd()`.
- `*vmf->pmd` neither none nor huge: `dax_iomap_pmd_fault()` returns 0 after
  `dax_unlock_entry()`; this is not a fallback.
- `fallback:` label: calls `split_huge_pmd()` and
  `count_vm_event(THP_FAULT_FALLBACK)` only when `ret` is
  `VM_FAULT_FALLBACK`; nothing else touches the page table.
- `grab_mapping_entry()` returning `VM_FAULT_OOM` or `VM_FAULT_SIGBUS`: jumps
  to `fallback:` too, and the split is skipped.
- `split_huge_pmd()` on a DAX VMA: does nothing unless `*vmf->pmd` is huge;
  then `__split_huge_pmd_locked()` in `mm/huge_memory.c` clears the PMD and,
  unless it mapped the huge zero folio, drops the folio's rmap and reference.
  It builds no PTE table.
- `CONFIG_FS_DAX_PMD` off: `dax_iomap_pmd_fault()` is a stub that returns
  `VM_FAULT_FALLBACK`, and `dax_fault_check_fallback()` is not compiled.
- `CONFIG_FS_DAX_PMD`: has no prompt; see `fs/Kconfig` for what it depends
  on.
