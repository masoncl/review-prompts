- `kvm->arch.nested_mmus`: an array of pointers (`struct kvm_s2_mmu **`),
  allocated once by `kvm_init_nested()` for `KVM_MAX_VCPUS *
  S2_MMU_PER_VCPU` entries, for every VM. It is never reallocated.
- `kvm_vcpu_init_nested()`: allocates one chunk of `S2_MMU_PER_VCPU`
  structs, initialises them, then publishes the pointers and raises
  `nested_mmus_size` under the `mmu_lock` write lock.
- A `struct kvm_s2_mmu` never moves once published; there is no fix-up of
  back pointers.
- Invalid marker: `VTTBR_CNP_BIT` set in `tlb_vttbr`, tested by
  `kvm_s2_mmu_valid()`. `kvm_init_nested_s2_mmu()` sets it, called from
  `kvm_init_stage2_mmu()` and from `kvm_free_stage2_pgd()`.
- `lookup_s2_mmu()` with guest stage 2 enabled: needs full VTTBR (CnP
  masked) and VTCR equal, on an entry that is also enabled.
- `lookup_s2_mmu()` with guest stage 2 disabled: needs only the VMID equal,
  on an entry that is also disabled.
- Recycling in `get_s2_mmu_nested()`: round-robin from `nested_mmus_next`,
  first entry with `refcnt == 0`, valid or not; `BUG_ON()` if none.
- `kvm_vcpu_put_hw_mmu()`: keeps the reference and `vcpu->arch.hw_mmu` when
  `vcpu->scheduled_out` is set and `IN_WFI` is clear.
- `kvm_vcpu_load_hw_mmu()`: does no lookup when `hw_mmu` is already set.
- `refcnt` therefore counts vCPUs whose `hw_mmu` points at the MMU,
  including preempted ones.
- `pending_unmap`: set only in `get_s2_mmu_nested()`, when the recycled
  entry was valid. No notifier path sets or reads it.
- Recycling does not unmap: the entry gets its new `tlb_vttbr`, `tlb_vtcr`
  and `nested_stage2_enabled` at once, with the old mappings still present.
- `check_nested_vcpu_requests()`, on `KVM_REQ_NESTED_S2_UNMAP` with
  `pending_unmap` set: unmaps the full range of `vcpu->arch.hw_mmu` with
  `may_block` true before guest entry, and clears `pending_unmap`.
- `kvm_nested_s2_unmap()`: passes its `may_block` argument straight to
  `kvm_stage2_unmap_range()` for each valid MMU; it defers nothing.
- `kvm_nested_s2_unmap()` and `kvm_nested_s2_wp()`: also call
  `kvm_invalidate_vncr_ipa_all()`. `kvm_nested_s2_flush()` does not.
- All three return at once when `nested_mmus_size` is 0, so the first two
  then skip that call.
- `kvm_age_gfn()` and `kvm_test_age_gfn()` in `arch/arm64/kvm/mmu.c`: act
  on `kvm->arch.mmu` only; shadow MMUs are not aged.
- `kvm_arch_flush_shadow_all()`: calls `kvm_free_stage2_pgd()` on each
  shadow, skipping with `WARN_ON()` any with non-zero `refcnt`, then
  `kvm_uninit_stage2_mmu()`. It does not free the structs or the array.
- `kvm_destroy_nested()`, from `kvm_arch_destroy_vm()`: frees the chunks
  and the pointer array.
