- Three places hold PPI state, not two: the `struct vgic_irq` entries of
  `private_irqs[]`, `struct vgic_v5_cpu_if`, and `vgic_v5_ppi_state` in
  `struct kvm_host_data`.
- `vgic_v5_ppi_state`: guest state staged per physical CPU
  (`host_data_ptr()`), not host state; it has one `pendr`, used for entry and
  for exit, and `activer_exit`.
- `struct vgic_v5_cpu_if`: defined in `include/kvm/arm_vgic.h`; has no
  pending and no handling-mode field.

| Point | What moves | Current afterwards |
|---|---|---|
| load, `vgic_v5_load()` | VMCR and APR to hardware; no PPI state | PPI state still in memory |
| entry, `vgic_v5_flush_ppi_state()` then `__vgic_v5_restore_ppi_state()` | pending from `struct vgic_irq` via `pendr`; DVI, active, enable, priority from `struct vgic_v5_cpu_if` | hardware |
| exit, `__vgic_v5_save_ppi_state()` then `vgic_v5_fold_ppi_state()` | active and pending to `vgic_v5_ppi_state`, priority to `struct vgic_v5_cpu_if`, then folded into `struct vgic_irq` | memory |
| put, `vgic_v5_put()` | APR from hardware; no PPI register is read | memory |
