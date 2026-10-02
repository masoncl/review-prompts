- `can_change_pte_writable()`: common vetoes are in
  `maybe_change_pte_writable()`; the mapping-specific halves are
  `can_change_private_pte_writable()` and `can_change_shared_pte_writable()`.
- mprotect does not call `can_change_pte_writable()`; see
  `set_write_prot_commit_flush_ptes()` in `mm/mprotect.c`.
- `VM_PFNMAP` and `VM_MIXEDMAP`: no exemption. Private: `vm_normal_page()`
  returns NULL for a special entry when the VMA has no `find_normal_page`, so
  that entry is never upgraded. Shared: `pte_dirty()` decides.
- Shared writable VMA where `vma_wants_writenotify()` is false: `vm_page_prot`
  is already writable, so writable-and-clean is legal; `set_pte_range()` sets
  dirty on a read fault only if `folio_test_dirty()`.
- Zero page: the `VM_WARN_ON_ONCE()` against a dirty zero-page entry is in
  `can_change_shared_pte_writable()` only. In a private VMA `replace_page()` in
  `mm/ksm.c` maps the zero page dirty as a marker; `is_ksm_zero_pte()` tests it.
- Anonymous fault: `map_anon_folio_pte_nopf()` sets write and dirty together,
  and only when the VMA has `VM_WRITE`.
- x86: Write=0 with Dirty=1 is the shadow-stack encoding. `pte_wrprotect()`
  moves dirty to `_PAGE_SAVED_DIRTY`, `pte_dirty()` tests both bits, and
  `pte_mkwrite()` picks the encoding from `VM_SHADOW_STACK`.
- **Unsafe usage**: deciding the write upgrade for a batch of entries of one
  anon large folio from `PageAnonExclusive()` of the first page.
  - Safe: split the batch into runs of equal exclusivity, as
    `commit_anon_folio_batch()` does.
