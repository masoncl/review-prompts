| Device | Skipped when | Registration failure |
|---|---|---|
| `KVM_DEV_TYPE_ARM_VGIC_V5` | `is_protected_kvm_enabled()` | tolerated, probe continues |
| `KVM_DEV_TYPE_ARM_VGIC_V3` | `!cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)` | returned, even if the GICv5 device registered |

- `-ENODEV`: returned only when the legacy cpucap is absent and the GICv5
  device was not registered.
- `KVM_DEV_TYPE_ARM_VGIC_V3` registration: `kvm_register_vgic_device()` also
  registers the ITS device, so an ITS registration failure fails the probe.
- `max_gic_vcpus`: `VGIC_V5_MAX_CPUS` on the non-pKVM path; overwritten with
  `min(VGIC_V3_MAX_CPUS, VGIC_V5_MAX_CPUS)` once the GICv3 device registered.
- `VGIC_V3_MAX_CPUS` and `VGIC_V5_MAX_CPUS`: both 512 in
  `include/kvm/arm_vgic.h`.
- `vgic_v5_get_implemented_ppis()`: fills `impl_ppi_mask`; skipped under pKVM
  together with the GICv5 registration.
- `nr_lr`: `(vgic_ich_vtr() & 0xf) + 1`; the probe does not call
  `__vgic_v3_get_gic_config()`.
- `kvm_vgic_global_state.type`: set to `VGIC_V5` first and stays so, even when
  only the GICv3 device ends up registered.
- `gicv3_cpuif` static key and `vgic_v3_enable_cpuif_traps()`: done inside
  `vgic_v5_probe()` on the compat path, not in `kvm_vgic_hyp_init()`.
