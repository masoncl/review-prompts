- **Unsafe usage**: calling, between the locked check and the install, a
  helper that may yield `mmu_lock`.
  - Unsafe: `kvm_mmu_invalidate_start()` asserts the write lock, so the
    check holds only while the lock is held.
  - Safe: call it in its no-yield mode, as `FNAME(fetch)` does with
    `mmu_sync_children(vcpu, sp, false)`; on contention that returns
    `-EINTR` and the fault returns `RET_PF_RETRY`.
- **Potentially unsafe usage**: making the last check before install without
  `mmu_lock`.
  - Unsafe: when the lock held instead is not one the unmap path takes for
    that gfn; an invalidation can then start after the check.
  - Safe: under `lock_rmap()` on the gfn's rmap entry, with the HPTE put on
    that rmap chain under the same hold, as `kvmppc_do_h_enter()` does;
    `kvm_unmap_rmapp()` takes that lock for each gfn it unmaps.
- **Potentially unsafe usage**: returning for retry after
  `mmu_invalidate_retry_gfn_unsafe()` fires.
  - Unsafe: after the frame was resolved, without releasing the page.
  - Safe: before the lookup, when no page is held, as the first check in
    `kvm_mmu_faultin_pfn()`.
  - Safe: after the lookup, releasing the page as unused first, as
    `kvm_mmu_faultin_pfn()` does through `kvm_mmu_finish_page_fault()` and
    `kvm_s390_faultin_gfn()` does through `kvm_release_faultin_page()`.
- Retry inside the kernel: allowed if the lock is dropped, the page released
  and the snapshot taken again; loongarch `kvm_map_page()` and
  `kvm_s390_faultin_gfn()` loop this way.
- Users that are not fault handlers follow the same order: for example
  `vmx_set_apic_access_page_addr()` and `__sev_snp_reload_vmsa()`, which
  request a reload on retry.
