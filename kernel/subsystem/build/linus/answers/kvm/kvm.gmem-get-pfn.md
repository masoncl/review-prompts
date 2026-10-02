- There is no kvm_arch_gmem_prepare(), kvm_gmem_prepare_folio() or
  CONFIG_HAVE_KVM_ARCH_GMEM_PREPARE here; the hook is
  `kvm_arch_gmem_make_private()` under `CONFIG_HAVE_KVM_ARCH_GMEM_CONVERT`,
  called directly from `kvm_gmem_get_pfn()` with the folio locked.
- `kvm_arch_gmem_make_private()`: runs on every `kvm_gmem_get_pfn()` call
  where `kvm_gmem_is_private_mem()` holds, whether or not the folio is
  uptodate, so an implementation must tolerate repeat calls.
- x86 implementation `sev_gmem_make_private()` in `arch/x86/kvm/svm/sev.c`:
  returns 0 for a non-SNP VM, and for an RMP entry already assigned.
- `folio_test_uptodate()`: gates only `clear_highpage()` and
  `folio_mark_uptodate()` in `kvm_gmem_get_pfn()`; it says nothing about the
  hook.
- Hook failure: the folio reference is dropped and the error returned;
  `*pfn` has already been written, `*page` has not.
- `max_order`: may be NULL; `kvm_gmem_get_pfn()` substitutes a local.
- `kvm_gmem_populate()`: goes through `__kvm_gmem_get_pfn()`, so it runs no
  hook and no zeroing; it marks the folio uptodate after `post_populate`
  succeeds, under `filemap_invalidate_lock()`.
- There is no kvm_arch_gmem_invalidate() here. `kvm_arch_gmem_reclaim()`
  (`CONFIG_HAVE_KVM_ARCH_GMEM_RECLAIM`) runs from `kvm_gmem_free_folio()`.
- `kvm_arch_gmem_invalidate_range()` (`CONFIG_HAVE_KVM_ARCH_GMEM_INVALIDATE`):
  a separate hook, run under `mmu_lock` from `__kvm_gmem_invalidate_start()`
  and from x86 `kvm_arch_flush_shadow_memslot()`.
- `get_file_active()` protects the file only; the memslot stays valid
  because the caller is inside `kvm->srcu` or holds `kvm->slots_lock`.
