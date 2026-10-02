- arm64 `user_mem_abort()` holds none of the steps itself; the helpers below
  hold them.

| Step | arm64, `arch/arm64/kvm/mmu.c` |
|---|---|
| snapshot | `kvm_s2_fault_get_vma_info()`, into `s2vi->mmu_seq`; called from `kvm_s2_fault_pin_pfn()`, not from `user_mem_abort()` |
| barrier | no `smp_rmb()` call; `mmap_read_unlock()` is the next statement |
| resolve | `kvm_s2_fault_pin_pfn()`, with `__kvm_faultin_pfn()` |
| lock, check, install, release | `kvm_s2_fault_map()` |

- `kvm_s2_fault_get_vma_info()`: reads the VMA data before the snapshot, both
  under `mmap_read_lock()`.
- `kvm_s2_fault_compute_prot()` non-zero return: runs between resolve and
  lock; `user_mem_abort()` then releases with `kvm_release_page_unused()`.
- `kvm_fault_lock()`: read lock, or write lock when
  `is_protected_kvm_enabled()`.
- `gmem_abort()`: used when `kvm_slot_has_gmem()` and the VM is not
  `kvm_vm_is_protected()`; all steps in one function, with an explicit
  `smp_rmb()` and `kvm_gmem_get_pfn()`.
- `pkvm_mem_abort()`: used when `kvm_vm_is_protected()`; takes no snapshot and
  makes no retry check; it pins with `pin_user_pages()` and `FOLL_LONGTERM`,
  and arm64 `kvm_unmap_gfn_range()` returns early for such a VM.
- There is no __gfn_to_pfn_memslot() here; `__kvm_faultin_pfn()` in
  `virt/kvm/kvm_main.c` resolves the frame.
- x86 shadow paging: `FNAME(page_fault)` in `arch/x86/kvm/mmu/paging_tmpl.h`
  takes the write lock, checks, and installs with `FNAME(fetch)`.
- x86 lock mode: `kvm_tdp_mmu_page_fault()` read; `direct_page_fault()` and
  `FNAME(page_fault)` write.
- x86 `kvm_mmu_faultin_pfn()`: reads `kvm_mem_is_private()` after the
  snapshot, so an attribute change is caught by the same check.
