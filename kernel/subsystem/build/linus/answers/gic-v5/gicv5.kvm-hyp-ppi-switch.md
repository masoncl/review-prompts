- State kept: bank 0 only, enforced by
  `BUILD_BUG_ON(VGIC_V5_NR_PRIVATE_IRQS != 64)`, plus priority registers 0 to 7.
- `__vgic_v5_save_ppi_state()`, in order:
  1. read `SYS_ICH_PPI_ACTIVER0_EL2` into `activer_exit`
  2. read `SYS_ICH_PPI_PENDR0_EL2` into `pendr`
  3. read `SYS_ICH_PPI_PRIORITYR0_EL2` to `SYS_ICH_PPI_PRIORITYR7_EL2` into
     `cpu_if->vgic_ppi_priorityr[]`
  4. write 0 to `SYS_ICH_PPI_DVIR0_EL2` and `SYS_ICH_PPI_DVIR1_EL2`
- Not read on save: the enable and DVI registers. `vgic_ppi_enabler` is
  updated by the trap handler `access_gicv5_ppi_enabler()` in
  `arch/arm64/kvm/sys_regs.c`.
- `__vgic_v5_restore_ppi_state()`, in order:
  1. `SYS_ICH_PPI_DVIR0_EL2` from `vgic_ppi_dvir`
  2. `SYS_ICH_PPI_ACTIVER0_EL2` from `vgic_ppi_activer`
  3. `SYS_ICH_PPI_ENABLER0_EL2` from `vgic_ppi_enabler`
  4. `SYS_ICH_PPI_PENDR0_EL2` from `pendr` AND NOT `vgic_ppi_dvir`
  5. `SYS_ICH_PPI_PRIORITYR0_EL2` to `SYS_ICH_PPI_PRIORITYR7_EL2`
  6. write 0 to `SYS_ICH_PPI_DVIR1_EL2`, `SYS_ICH_PPI_ACTIVER1_EL2`,
     `SYS_ICH_PPI_ENABLER1_EL2`, `SYS_ICH_PPI_PENDR1_EL2`, and
     `SYS_ICH_PPI_PRIORITYR8_EL2` to `SYS_ICH_PPI_PRIORITYR15_EL2`
- nVHE: `__hyp_vgic_save_state()` and `__hyp_vgic_restore_state()` in
  `arch/arm64/kvm/hyp/nvhe/switch.c`.
- VHE: nothing in `arch/arm64/kvm/hyp/vhe/switch.c` calls them. The kernel
  wrappers `vgic_v5_save_state()` and `vgic_v5_restore_state()` in
  `arch/arm64/kvm/vgic/vgic-v5.c` do, and add a `dsb(sy)`.
- The wrappers are reached from `vgic_save_state()` and
  `vgic_restore_state()` in `arch/arm64/kvm/vgic/vgic.c`, gated by
  `can_access_vgic_from_kernel()`: in `kvm_vgic_sync_hwstate()` before the
  fold, and in `kvm_vgic_flush_hwstate()` after the flush.
- On both paths `__vgic_v5_save_state()` or `__vgic_v5_restore_state()` runs
  just before the PPI function.
