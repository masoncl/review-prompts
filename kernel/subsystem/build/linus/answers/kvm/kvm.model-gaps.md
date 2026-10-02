- Models take an x86 memslot delete or move to always toggle `mmu_valid_gen`.
  When its `zap_all` condition is false, `kvm_arch_flush_shadow_memslot()`
  calls `kvm_unmap_gfn_range()` and `kvm_mmu_zap_memslot_pages_and_flush()`
  instead of the fast zap.
- Models take the x86 fast zap to be one function. `kvm_mmu_zap_all_fast()`
  calls `__kvm_mmu_zap_all_fast_front_half()` under `mmu_lock`, then
  `__kvm_mmu_zap_all_fast_back_half()`, which asserts `mmu_lock` is not held.
- Models take `struct kvm_gfn_range` to carry only slot, range, `arg` and
  `may_block`. It also has `attr_filter` and `lockless`.
  `kvm_handle_hva_range()` sets `KVM_FILTER_SHARED`; guest_memfd takes the
  filter from `kvm_gmem_get_invalidate_filter()`.
- Models take `GUEST_MEMFD_FLAG_INIT_SHARED` to be accepted on any VM. x86
  `kvm_arch_supports_gmem_init_shared()` returns false for a VM with private
  memory, and `kvm_gmem_create()` then fails with `-EINVAL`.
- Models take the review checklist to hold more than it does.
  `Documentation/virt/kvm/review-checklist.rst` has eleven items and a
  section on testing.
- Models miss that `kvm_mmu_child_role()` clears `passthrough` in the child
  role, as well as `invalid`.
- Models take `struct kvm_mmu` to hold the guest paging mode and walk
  callbacks. Those are in `struct kvm_pagewalk`, reached through `mmu->w`,
  which points at `vcpu->arch.gva_walk` or `vcpu->arch.ngpa_walk`; see
  `arch/x86/include/asm/kvm_host.h`.
