- pKVM host: `kvm_pkvm_ext_allowed()` in
  `arch/arm64/include/asm/kvm_pkvm.h` returns false for `KVM_CAP_ARM_MTE`, so
  `kvm_vm_ioctl_enable_cap()` returns `-EINVAL` for every VM when
  `is_protected_kvm_enabled()`.
- guest_memfd, both directions:
  - enabling the cap returns `-EINVAL` if any existing memslot has
    `kvm_slot_has_gmem()`;
  - `kvm_arch_prepare_memory_region()` returns `-EINVAL` for a gmem slot once
    `kvm_has_mte()`.
- Locks for enabling: `kvm->lock`, then `kvm->slots_lock` for the memslot
  scan.
- AArch32: `kvm_vcpu_init_check_features()` in `arch/arm64/kvm/arm.c` returns
  `-EINVAL` for `KVM_ARM_VCPU_EL1_32BIT` when `kvm_has_mte()`; there is no
  vcpu_allowed_register_width().
- Fault path condition, same for the refusal and for the tag clearing: not a
  permission fault, `!s2vi->map_non_cacheable`, and `kvm_has_mte()`. The test
  is not on `s2vi->device`.
- Non-cacheable PFNMAP fault with MTE on: the MTE test is skipped, the fault
  is not refused by it.
- Refusal (`!s2vi->mte_allowed`, `-EFAULT`): in `kvm_s2_fault_compute_prot()`,
  before `mmu_lock`.
- `sanitise_mte_tags()`: called only from `kvm_s2_fault_map()`, under
  `mmu_lock`, on the mapping size after `transparent_hugepage_adjust()`.
- `sanitise_mte_tags()`: returns at once for `is_zero_pfn()`; does not call
  `mte_sync_tags()`.
- `gmem_abort()` and `pkvm_mem_abort()`: no tag check and no call to
  `sanitise_mte_tags()`; the exclusions above keep MTE VMs off both paths.
