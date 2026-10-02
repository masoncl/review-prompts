- `is_error_noslot_pfn()`: true for every `KVM_PFN_ERR_` value and for
  `KVM_PFN_NOSLOT`; it tests `KVM_PFN_ERR_NOSLOT_MASK`.
- `is_error_pfn()`: false for `KVM_PFN_NOSLOT`; a caller that tests only this
  takes a no-slot frame for a real frame.
- `is_sigpending_pfn()`: true only for `KVM_PFN_ERR_SIGPENDING`.
- `KVM_PFN_ERR_NEEDS_IO`: has no predicate; callers compare the value
  directly.
  - Returned only when the caller passed `FOLL_NOWAIT`, so
    `kvm_faultin_pfn()` never returns it.
  - Caller sets up an async fault or calls again without `FOLL_NOWAIT`; see
    `__kvm_mmu_faultin_pfn()` and `kvm_s390_faultin_gfn()`.
- `KVM_PFN_ERR_SIGPENDING`: `hva_to_pfn()` returns it for any `-EINTR` or
  `-EAGAIN` from `hva_to_pfn_slow()`; it does not test `FOLL_INTERRUPTIBLE`
  itself.
- `KVM_PFN_NOSLOT`: `kvm_follow_pfn()` also returns it for a slot flagged
  `KVM_MEMSLOT_INVALID`, which is not MMIO.
  - x86 `kvm_mmu_faultin_pfn()` tests `KVM_MEMSLOT_INVALID` before the call
    and retries the fault.
- `KVM_PFN_ERR_RO_FAULT`: also returned by `hva_to_pfn_remapped()` for a write
  fault on a non-writable `VM_IO` or `VM_PFNMAP` mapping, in a slot that is
  not read-only.
- `KVM_HVA_ERR_BAD` and `KVM_HVA_ERR_RO_BAD`: no predicate tells them apart;
  compare with `== KVM_HVA_ERR_RO_BAD`, as `kvm_follow_pfn()` does.
- Overrides of both hva values and of `kvm_is_error_hva()`: an architecture
  defines `KVM_HVA_ERR_BAD` itself; search for the name. For example s390, in
  `arch/s390/include/asm/kvm_host_s390.h`, uses `-1UL`, `-2UL` and
  `IS_ERR_VALUE()`.
