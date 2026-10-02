- There is no vgic_v3_vmcr_sync() and no __vgic_v3_save_vmcr_aprs() here; no
  code reads `ICH_VMCR_EL2` at put.

| Direction | GICv3 guest (`vgic_sre` set) | GICv2 guest (`vgic_sre` clear) |
|---|---|---|
| hardware to `vgic_vmcr` | every exit, `__vgic_v3_save_state()` | every exit, same function |
| `vgic_vmcr` to hardware | load, `__vgic_v3_restore_vmcr_aprs()` | `__vgic_v3_activate_traps()`: load with VHE, every entry without |

- `__vgic_v3_save_state()`: reads `ICH_VMCR_EL2` unconditionally; with VHE it
  runs from `kvm_vgic_sync_hwstate()`, without VHE from
  `__hyp_vgic_save_state()`.
- `__vgic_v3_restore_vmcr_aprs()`: skips the VMCR write when `vgic_sre` is
  clear, and still restores the APRs.
- `__vgic_v3_activate_traps()`: writes the VMCR only when `vgic_sre` is clear
  and `vgic_hcr` has `ICH_HCR_EL2_En`.
- `__vgic_v3_deactivate_traps()`: does not read or write the VMCR.
- `vgic_get_vmcr()` in `arch/arm64/kvm/vgic/vgic-mmio.c`: switches on
  `vgic_model`, not on `kvm_vgic_global_state.type`.
- GICv2 model on a GICv3 CPU interface: `vgic_get_vmcr()` calls
  `vgic_v3_get_vmcr()`, which decodes `vgic_v3.vgic_vmcr`; `vgic_v2_get_vmcr()`
  is used only on GICv2 hardware.
- `vgic_vmcr` outside the guest: equals the hardware value as of the last
  exit; no extra sync is needed before `vgic_get_vmcr()`.
- pKVM, write to hardware: `kvm_arch_vcpu_load()` issues the
  `__vgic_v3_restore_vmcr_aprs` hypercall; `handle___vgic_v3_restore_vmcr_aprs()`
  copies the host `vgic_vmcr` into the hyp vCPU first.
- pKVM, save: `__vgic_v3_save_state()` fills the hyp copy at each exit;
  `sync_hyp_vgic_state()` copies it to the host after each run.
- Nested state: `vgic_v3_sync_nested()` reads `ICH_VMCR_EL2` into the vCPU's
  `ICH_VMCR_EL2` sysreg at each exit; `vgic_v3_load_nested()` loads the
  shadow built from that sysreg; `vgic_vmcr` of the vCPU is not touched.
