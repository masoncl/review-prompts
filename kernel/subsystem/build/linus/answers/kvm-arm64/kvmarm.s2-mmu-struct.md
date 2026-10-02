- `kvm_vcpu_load_hw_mmu()` in `arch/arm64/kvm/nested.c`: picks
  `&kvm->arch.mmu` only when `is_hyp_ctxt()`; every other context gets a
  shadow from `get_s2_mmu_nested()`, also when the guest's `HCR_EL2.VM` is
  clear.
- Guest `HCR_EL2.VM` clear: `lookup_s2_mmu()` matches a shadow with
  `nested_stage2_enabled` false by VMID alone, and `kvm_handle_guest_abort()`
  skips `kvm_walk_nested_s2()` for it.
- `get_s2_mmu_nested()` runs under `write_lock(&kvm->mmu_lock)`.
- pKVM: `kvm_arch_vcpu_load()` jumps past the selection; EL2 sets its own
  `hw_mmu` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- There is no kvm_s2_mmu_nested and no nested_revmap in this tree.
- `split_page_cache` and `split_page_chunk_size`: read only on
  `kvm->arch.mmu`; on a shadow `kvm_init_stage2_mmu()` only initialises them.
- `shadow_pt_debugfs_dentry` (under `CONFIG_PTDUMP_STAGE2_DEBUGFS`): shadow
  only.
