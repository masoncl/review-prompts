- Private mapping: has a lock only if `__vma_private_lock()` is true, which
  needs a reservation map pointer and `HPAGE_RESV_OWNER`.
- Private VMA without `HPAGE_RESV_OWNER`, such as a child after fork: no lock;
  every lock helper returns without doing anything.
- Shared VMA at final unmap: `__hugetlb_zap_end()` with `ZAP_FLAG_UNMAP` calls
  `__hugetlb_vma_unlock_write_free()`, which clears `vm_private_data` before
  `i_mmap_rwsem` is dropped; from then on the VMA has no lock.
