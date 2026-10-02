- There is no kvm_mmu_faultin_pfn_private() and no fault_from_gmem() here;
  `__kvm_mmu_faultin_pfn()` in `arch/x86/kvm/mmu/mmu.c` open-codes
  `fault->is_private || kvm_memslot_is_gmem_only(fault->slot)` and calls
  `kvm_mmu_faultin_pfn_gmem()`.
- `KVM_MEMSLOT_GMEM_ONLY`: set by `kvm_gmem_bind()` when the inode has
  `GUEST_MEMFD_FLAG_MMAP`; shared faults on such a slot use guest_memfd too.
- `fault->is_private`: always `err & PFERR_PRIVATE_ACCESS` in
  `kvm_mmu_do_page_fault()`; for `KVM_X86_SW_PROTECTED_VM`,
  `kvm_mmu_page_fault()` sets that bit from `kvm_mem_is_private()`.
- `kvm_gmem_get_pfn()` failure in `kvm_mmu_faultin_pfn_gmem()`: prepares the
  memory-fault exit and returns the error unchanged, for example
  `-EHWPOISON`, not only `-EFAULT`.
- There is no private_max_mapping_level hook here; the op is
  `gmem_max_mapping_level`, called from `kvm_gmem_max_mapping_level()` via
  `kvm_mmu_max_mapping_level()`, not from `kvm_mmu_faultin_pfn_gmem()`.
- Mapping level of a guest_memfd fault: `fault->max_level` is
  `PG_LEVEL_4K`, because `__kvm_gmem_get_pfn()` always reports order 0.
