- `__kvm_faultin_pfn()`: both `writable` and `refcounted_page` must be
  non-NULL; otherwise `WARN_ON_ONCE()` and `KVM_PFN_ERR_FAULT`.
- There are no kvm_release_pfn_clean() or kvm_release_pfn_dirty() helpers
  here; release is by `struct page`: `kvm_release_faultin_page()`,
  `kvm_release_page_unused()`, `kvm_release_page_clean()`,
  `kvm_release_page_dirty()`.
- `kvm_release_faultin_page(kvm, page, unused, dirty)`: runs
  `lockdep_assert_once(lockdep_is_held(&kvm->mmu_lock) || unused)` before it
  tests `page` for NULL.
- **Potentially unsafe usage**: calling `kvm_release_faultin_page()` without
  `kvm->mmu_lock`.
  - Unsafe: with `unused` false; the assertion fires even for a NULL page.
  - Safe: with `unused` true, as `kvm_s2_fault_pin_pfn()` in
    `arch/arm64/kvm/mmu.c` does on its error path.
- `mmu_lock` held for read satisfies the assertion; `kvm_s2_fault_map()` holds
  it through `kvm_fault_lock()`, and `kvm_s390_faultin_gfn()` holds it for
  read.
