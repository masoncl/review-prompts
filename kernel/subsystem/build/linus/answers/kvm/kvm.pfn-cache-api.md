- Users in this tree: only x86 selects `HAVE_KVM_PFNCACHE`; the caches are the
  Xen ones in `arch/x86/kvm/xen.c` and `pv_time` for kvmclock.
- Steal time uses `struct gfn_to_hva_cache`, and the nested posted-interrupt
  descriptor uses `struct kvm_host_map`; neither is a pfn cache.
- `kvm_gpc_mark_dirty_in_slot()` in `include/linux/kvm_host.h`: what users
  call after a write; it asserts `gpc->lock` and does nothing for a cache
  activated by hva.
- `kvm_gpc_check()`, and `kvm_gpc_refresh()` for a cache activated by gpa,
  call `kvm_memslots()`, so the caller holds `kvm->srcu`;
  `kvm_xen_set_evtchn_fast()` and `kvm_xen_set_evtchn()` take it explicitly.
- `kvm_gpc_refresh()`: resolves the hva through `current->mm`, so a caller
  outside the VM's tasks adopts `kvm->mm` first; `kvm_xen_set_evtchn()` does
  it with `kthread_use_mm()`.
- **Unsafe usage**: accessing `gpc->khva` without `gpc->lock` because the
  vCPU is in guest mode, as the kerneldoc of `kvm_gpc_check()` allows;
  `gfn_to_pfn_cache_invalidate_start()` only clears `valid` and kicks no vCPU.
  - Safe: hold `gpc->lock` for read from `kvm_gpc_check()` to the last
    access, as `kvm_setup_guest_pvclock()` does;
    `gfn_to_pfn_cache_invalidate_start()` takes it for write to clear
    `valid`.
