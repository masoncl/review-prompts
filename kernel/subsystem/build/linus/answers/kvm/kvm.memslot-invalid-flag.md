- Test order in `kvm_mmu_faultin_pfn()`: alias, private/shared mismatch,
  `!slot`, then the flag.
- No slot versus INVALID slot in `kvm_mmu_faultin_pfn()`: `!slot` goes to
  `kvm_handle_noslot_fault()`; an INVALID slot returns `RET_PF_RETRY` and
  does not reach `kvm_handle_noslot_fault()`.
- `fault->prefetch` with an INVALID slot: returns `-EAGAIN`.
- `fault->prefetch` in `kvm_mmu_faultin_pfn()`: true for faults from
  `kvm_tdp_page_prefault()` and `kvm_arch_async_page_ready()`.
- Retry loop inside one SRCU read section: must stop on the flag, as the
  updater is waiting in `synchronize_srcu_expedited()`; see
  `tdx_handle_ept_violation()`.
- Lookups: `gfn_to_memslot()`, `kvm_vcpu_gfn_to_memslot()` and
  `id_to_memslot()` return a slot that has the flag set.
- INVALID copy: `kvm_copy_memslot()` does not copy `gmem`, so `gmem.file` is
  NULL and `kvm_gmem_get_pfn()` returns `-EFAULT`.
- **Potentially unsafe usage**: translating a gfn through a slot without
  testing `KVM_MEMSLOT_INVALID`.
  - Unsafe: `__gfn_to_hva_memslot()` on a slot from a lookup, to create a
    mapping, when nothing earlier on the path tested the flag; the copy
    keeps the old `userspace_addr`, so a mapping appears after the zap.
  - Safe: `gfn_to_hva_memslot()` and `gfn_to_hva_memslot_prot()`, which go
    through `__gfn_to_hva_many()` and return `KVM_HVA_ERR_BAD`.
  - Safe: after an explicit test, as `kvm_mmu_faultin_pfn()` does before
    `__kvm_mmu_faultin_pfn()`, and as `kvmppc_do_h_enter()` does before
    `__gfn_to_hva_memslot()`.
