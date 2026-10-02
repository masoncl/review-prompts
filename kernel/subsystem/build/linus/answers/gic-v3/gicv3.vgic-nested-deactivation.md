- Deactivation call: `vgic_v3_sync_nested()` passes the pINTID field of
  L1's LR to `vgic_v3_deactivate()` in `arch/arm64/kvm/vgic/vgic-v3.c`, the
  same function that handles a trapped `ICC_DIR_EL1` write.
- Which HW bit is tested: `ICH_LR_HW` and a non-zero state in L1's
  in-memory LR as it was before the write-back, plus a zero state in the
  hardware LR; so it also runs for an entry whose shadow LR had `ICH_LR_HW`
  cleared by `translate_lr_pintid()`.
- `vgic_v3_deactivate()` returns without touching the interrupt unless L1's
  own `vgic_vmcr` (in `vcpu->arch.vgic_cpu.vgic_v3`) has
  `ICH_VMCR_EL2_VEOIM_MASK` set and the INTID is below
  `nr_spis + VGIC_NR_PRIVATE_IRQS`.
- Physical side: when `vgic_state_is_nested()`, `vgic_v3_deactivate()` skips
  `vgic_v3_deactivate_phys()`, because the HW bit of the shadow LR has
  already deactivated the host interrupt.
- After clearing the active state: `vgic_v3_deactivate()` folds a pseudo-LR
  with `vgic_v3_fold_lr()` and raises `KVM_REQ_VGIC_PROCESS_UPDATE` on the
  vCPU that holds the interrupt; it does not re-queue it itself.
- Host maintenance interrupt while L2 runs: `vgic_maintenance_handler()`
  calls `vgic_v3_handle_nested_maint_irq()`, which injects `mi_intid` into L1
  with level taken from the hardware `ICH_MISR_EL2` (not the computed one),
  then clears `ICH_HCR_EL2_En` in hardware.
- Every exit from L2: `vgic_v3_sync_nested()` writes 0 to hardware
  `ICH_HCR_EL2` and then calls `vgic_v3_nested_update_mi()`, which sets the
  level again from L1's in-memory registers.
