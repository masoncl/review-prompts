- Second test: `!sp && kvm_test_request(KVM_REQ_MMU_FREE_OBSOLETE_ROOTS,
  vcpu)`; `is_page_fault_stale()` does not test `VALID_PAGE()`.
- Third test: gated on `fault->slot`; a fault with no slot skips
  `mmu_invalidate_retry_gfn()`.
- `__kvm_mmu_zap_all_fast_front_half()`: toggles `mmu_valid_gen` between 0
  and 1, invalidates `KVM_DIRECT_ROOTS` only, and makes the request, all
  under one write-lock hold.
- Senders of `KVM_REQ_MMU_FREE_OBSOLETE_ROOTS`, the full set:
  - `__kvm_mmu_zap_all_fast_front_half()`, to all vCPUs
  - `__kvm_mmu_prepare_zap_page()`, to all vCPUs, when it zaps a page with
    non-zero `root_count` that was not already obsolete
  - `FNAME(fetch)`, to its own vCPU, when the root is a dummy root
- Zap-all on memslot delete or move: only when `kvm->arch.vm_type` is
  `KVM_X86_DEFAULT_VM` and `KVM_X86_QUIRK_SLOT_ZAP_ALL` is enabled.
- Slot-only zap: no `mmu_valid_gen` toggle and no `mmu_invalidate_seq` bump;
  `kvm_mmu_faultin_pfn()` catches it earlier by testing `KVM_MEMSLOT_INVALID`.
