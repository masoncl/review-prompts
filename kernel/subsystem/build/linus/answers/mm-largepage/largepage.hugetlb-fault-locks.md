- `unmap_ref_private()`: takes `i_mmap_lock_write()` itself; nothing else in
  `hugetlb_wp()` takes `i_mmap_rwsem`, and `hugetlb_wp()` takes no folio
  lock.
- Anon folio under a present PTE: locked only by `hugetlb_fault()`, with
  `folio_trylock()`, only when `folio_test_anon()` is true, and after
  `huge_pte_lock()`.
- File folio under a present PTE: enters `hugetlb_wp()` unlocked, despite the
  comment above `hugetlb_wp()`.
- Page cache folio in `hugetlb_no_page()`: locked before the page table lock,
  unlocked before the `hugetlb_wp()` call.
- `hugetlb_wp()`, `cow_from_owner` path: the anon folio lock stays held while
  the mutex and VMA lock are dropped, so `i_mmap_rwsem` is taken for write
  under a folio lock, the reverse of the hugetlbfs order listed in
  `mm/rmap.c`.
- Userfaultfd RWP branch in `hugetlb_fault()` (protnone PTE with
  `huge_pte_uffd()`): sync mode returns through `hugetlb_handle_userfault()`
  with `VM_UFFD_RWP`, dropping VMA lock and mutex; async mode takes only the
  page table lock.
