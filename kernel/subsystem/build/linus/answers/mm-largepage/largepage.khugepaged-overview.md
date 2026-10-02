- `khugepaged_enter_vma()`: registers when `MMF_VM_HUGEPAGE` is clear,
  `hugepage_enabled()` is true and `collapse_possible()` returns nonzero. There
  is no hugepage_pmd_enabled() in this tree.
- `collapse_possible()` on an anonymous VMA with `TVA_KHUGEPAGED`: asks for
  `THP_ORDERS_ALL_ANON`, so an mm is registered when any anonymous order is
  allowed for the VMA, not only PMD order.
- `hugepage_madvise()`: only edits the flags, does not call
  `khugepaged_enter_vma()`; `madvise_update_vma()` in `mm/madvise.c` does.
  `mm/shmem.c` has no call.
- `khugepaged_fork()`: when the parent has `MMF_VM_HUGEPAGE`, calls
  `__khugepaged_enter()` for the child, which allocates a new slot;
  `MMF_VM_HUGEPAGE` is not in `MMF_INIT_LEGACY_MASK`, so the flag is not
  inherited.
- Slot type: `struct mm_slot` from `mm_slot_alloc()`; there is no
  struct khugepaged_mm_slot.
- `__khugepaged_exit()` when the slot is the scan cursor: takes and releases
  `mmap_write_lock()` to wait for the daemon, frees nothing.
- `collect_mm_slot()`: frees the slot only when `collapse_test_exit()` sees
  `mm_users == 0`; it does not clear `MMF_VM_HUGEPAGE`.
- mm with `MMF_DISABLE_THP_COMPLETELY` or with no eligible VMA: the cursor moves
  past it, the slot stays on `khugepaged_scan.mm_head` until the mm exits.
- Function names in this tree; there is no khugepaged_scan_mm_slot(),
  hpage_collapse_scan_pmd(), hpage_collapse_scan_file() or
  hugepage_vma_check():

| Scope | Function |
|---|---|
| one mm | `collapse_scan_mm_slot()` |
| one PMD range, anon or file | `collapse_single_pmd()` |
| anon scan | `collapse_scan_pmd()` -> `mthp_collapse()` -> `collapse_huge_page()` |
| file scan | `collapse_scan_file()` -> `collapse_file()` |
| mm exiting | `collapse_test_exit()` |
| VMA filter | `collapse_possible()` |

- `collapse_scan_mm_slot()`: uses `mmap_read_trylock()`; on failure it moves
  the cursor to the next mm.
- `collapse_single_pmd()`: sends every non-anonymous VMA that passed
  `collapse_possible()` to `collapse_scan_file()`, shmem included;
  `madvise_collapse()` uses it too.
