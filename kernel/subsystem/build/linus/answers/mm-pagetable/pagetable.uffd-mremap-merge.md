- `mremap_userfaultfd_prep()`: defined in `mm/userfaultfd.c`; there is no
  fs/userfaultfd.c in this tree.
- `mremap_userfaultfd_prep()`: takes no range. Without
  `UFFD_FEATURE_EVENT_REMAP` it calls `userfaultfd_reset_ctx()` on the whole
  VMA, which clears `vm_userfaultfd_ctx` and all of `__VM_UFFD_FLAGS`.
- `copy_vma_and_data()` in `mm/mremap.c`: calls it after
  `move_page_tables()`, and only when the move succeeded.
- `move_page_tables()`: writes only `[new_addr, new_addr + old_len)` of the
  returned VMA.
- `copy_vma()`: returns either a fresh `vm_area_dup()` copy or an existing
  neighbour expanded by `vma_merge_copied_range()`.
- `is_mergeable_vma()` in `mm/vma.c`: compares the VMA flags and the context
  pointer; nothing on the merge path tests `UFFD_FEATURE_EVENT_REMAP`.
- `move_ptes()`, `move_huge_pmd()`, `move_huge_pte()`: read
  `vma_has_uffd_without_event_remap()` from the source VMA; when true they
  clear the bit, and for a present RWP entry restore `vma->vm_page_prot`.
  `move_ptes()` and `move_huge_pte()` also drop a `PTE_MARKER_UFFD_WP`.
- `uffd_supports_page_table_move()`: refuses `move_normal_pmd()` and
  `move_normal_pud()` if either VMA has a context without
  `UFFD_FEATURE_EVENT_REMAP`, so that the walk reaches every leaf entry.
- **Potentially unsafe usage**: resetting the context of the whole VMA that
  `copy_vma()` returned.
  - Unsafe: when that VMA covers populated addresses outside the moved
    range, as after a merge with a registered neighbour; those entries keep
    the bit, `PAGE_NONE` or the marker in a VMA with no uffd flag.
  - Safe: when `copy_vma()` took the `vm_area_dup()` branch; every populated
    entry of the new VMA was written by the move helpers above.
  - Safe: cleaning a range and then resetting only that range, as
    `userfaultfd_clear_vma()` does with `change_protection()` and
    `vma_modify_flags_uffd()`.
