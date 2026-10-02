- `kvm_pkvm_ext_allowed()`: static inline in
  `arch/arm64/include/asm/kvm_pkvm.h`; there is no kvm_pvm_ext_allowed.

| Capability | Result |
|---|---|
| ten listed in the first `case` group | true for every VM |
| `KVM_CAP_ARM_MTE` | false for every VM |
| `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`, `KVM_CAP_ARM_SUPPORTED_BLOCK_SIZES` | false for every VM |
| any other | true if `kvm` is NULL or the VM is not protected |

- `KVM_CAP_ARM_PMU_V3` and `KVM_CAP_ARM_SVE`: not in the listed group, so
  false for a protected VM.
- Protected VM features: the host's bitmap ANDed with `KVM_ARM_VCPU_PSCI_0_2`
  and the two `KVM_ARM_VCPU_PTRAUTH_ADDRESS`, `KVM_ARM_VCPU_PTRAUTH_GENERIC`
  bits; `KVM_ARM_VCPU_PMU_V3` and `KVM_ARM_VCPU_SVE` are dropped.
- Protected VM flags: start at 0 in `init_pkvm_hyp_vm()`;
  `KVM_ARCH_FLAG_MTE_ENABLED` is never copied.
- `KVM_ARCH_FLAG_GUEST_HAS_SVE`: assigned for both kinds of VM from EL2's
  resulting feature bitmap, not copied from the host flags.
- Non-protected VM flags: the host's `arch.flags` with
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED` cleared.
- Non-protected VM, `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS` set: only
  `midr_el1` is copied.
- `arch.vgic.vgic_model`: copied from the host for both kinds, like
  `ctr_el0`.
- There is no fixed_config.h or PVM_ID_AA64PFR0_ALLOW here; protected ID
  registers come from `kvm_init_pvm_id_regs()` in
  `arch/arm64/kvm/hyp/nvhe/sys_regs.c`.
- `kvm_pkvm_ioctl_allowed()`: maps a VM ioctl to a capability with
  `kvm_get_cap_for_kvm_ioctl()` and applies the same list.
