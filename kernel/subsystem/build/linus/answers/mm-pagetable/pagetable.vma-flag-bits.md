- `userfaultfd_clear_vma()`: does not call `uffd_wp_range()`; it calls
  `change_protection()` itself, when `userfaultfd_protected(vma)`.
- Flags passed: `MM_CP_UFFD_WP_RESOLVE` for a `VM_UFFD_WP` VMA,
  `MM_CP_UFFD_RWP_RESOLVE` for a `VM_UFFD_RWP` VMA, plus
  `MM_CP_TRY_CHANGE_WRITABLE` when `vma_wants_manual_pte_write_upgrade()`.
- `VM_UFFD_RWP` VMA: besides the bit, the `PAGE_NONE` protection must go;
  the same walk rewrites each present entry to `vma->vm_page_prot`.
- `vma_modify_flags_uffd()` and `userfaultfd_set_vm_flags()`: clear neither
  the bit nor `PAGE_NONE` from any entry; they only split or merge and
  change the VMA.
- `change_huge_pud()`: `WARN_ON_ONCE()` and skips for any uffd flag; there
  is no pud_uffd() or pud_mkuffd() here.
- `change_protection()`: `WARN_ON_ONCE()` and does nothing if WP and RWP
  flags are mixed, or a protect flag comes with its resolve flag.
- `userfaultfd_register()`: returns `-EBUSY` for a registration to the same
  context that would drop `VM_UFFD_WP` or `VM_UFFD_RWP` from a VMA; the
  mode can only change through unregister, hence through
  `userfaultfd_clear_vma()`.
- **Potentially unsafe usage**: clearing `VM_UFFD_WP` or `VM_UFFD_RWP` with
  `userfaultfd_reset_ctx()` directly.
  - Unsafe: when entries of the VMA still carry the bit, `PAGE_NONE` or a
    `PTE_MARKER_UFFD_WP`; a later registration reads them in its own mode,
    and `change_present_ptes()` turns a leftover bit into `PAGE_NONE` in a
    `VM_UFFD_RWP` VMA.
  - Safe: in `dup_userfaultfd()` on the child VMA before
    `copy_page_range()`; `__copy_present_ptes()` and `copy_pte_marker()`
    test the destination VMA and drop the bit and the marker.
  - Safe: through `userfaultfd_clear_vma()`, which walks `[start, end)`
    first.
