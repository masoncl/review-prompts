- Nested virtualisation: absent; `vgic_v5_init()` returns `-EINVAL` if any vCPU
  has `vcpu_has_nv()`.
- When the NV error surfaces: at `KVM_DEV_ARM_VGIC_CTRL_INIT` (through
  `vgic_init()`), not at device creation.
- NV with the GICv3 device on a GICv5 host: accepted; `init_subsystems()` in
  `arch/arm64/kvm/arm.c` allows `KVM_MODE_NV` when
  `kvm_vgic_global_state.has_gcie_v3_compat` is set.
- Protected KVM: absent; `vgic_v5_probe()` does not register
  `KVM_DEV_TYPE_ARM_VGIC_V5` when `is_protected_kvm_enabled()`.
- pKVM on a host without the legacy interface: `vgic_v5_probe()` returns
  `-ENODEV`, and `init_subsystems()` then fails KVM init.
- Save and restore to userspace: absent; `vgic_v5_set_attr()` and
  `vgic_v5_get_attr()` return `-ENXIO` for every group except
  `KVM_DEV_ARM_VGIC_GRP_CTRL`.
- `KVM_DEV_ARM_VGIC_GRP_CTRL` attributes: `KVM_DEV_ARM_VGIC_CTRL_INIT` and
  `KVM_DEV_ARM_VGIC_USERSPACE_PPIS`; the latter is get-only, a set returns
  `-ENXIO`.
