- `kvm_s2_fault_get_vma_info()`: samples `kvm->mmu_invalidate_seq` into
  `s2vi->mmu_seq`, last thing before `mmap_read_unlock()`.
- Sampled before the sequence read, under `mmap_read_lock()`: `vma_pagesize`,
  `max_map_size`, `gfn`, `mte_allowed`, `vm_flags`, `is_vma_cacheable`.
- Sampled after it, in `kvm_s2_fault_pin_pfn()`: `pfn`, `page`,
  `map_writable`, then `device` and `map_non_cacheable` derived from `pfn`,
  `vm_flags` and `is_vma_cacheable`.
- `vma`: local to `kvm_s2_fault_get_vma_info()`; nothing sets it to NULL, and
  later stages have no pointer to it.
- Barrier: the `user_mem_abort()` path has no explicit `smp_rmb()` after the
  read and relies on `mmap_read_unlock()`; `gmem_abort()` holds no mmap lock
  and has an explicit `smp_rmb()`.
- `mmu_invalidate_retry()`: checked in `kvm_s2_fault_map()`, first thing after
  `kvm_fault_lock()`.
- Not covered by the retry check: the error returns taken before the lock.
  `kvm_s2_fault_pin_pfn()` (`-EFAULT` for cacheable PFNMAP without
  `kvm_supports_cacheable_pfnmap()`) and `kvm_s2_fault_compute_prot()`
  (`-ENOEXEC`, `-EFAULT` for `!mte_allowed`) act on the sampled values
  unvalidated.
