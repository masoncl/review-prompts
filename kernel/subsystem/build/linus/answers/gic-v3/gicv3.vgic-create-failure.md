- Failure that reaches the cleanup: only `-ENOMEM` from
  `vgic_allocate_private_irqs_locked()`; the `-E2BIG` exit is before any vGIC
  field is written.
- Private IRQs: freed by an open-coded `kfree()` plus NULL store for every
  vCPU; `kvm_vgic_vcpu_destroy()` is not called.
- `vgic.vgic_model` and `vgic.in_kernel`: were written before the loop, and
  are reset to 0 and `false`.
- Resulting state: `irqchip_in_kernel()` is false, so a retry does not get
  `-EEXIST`.
- Not restored: `kvm->max_vcpus`, `vgic.implementation_rev`, the base
  addresses, and the ID register fields written by
  `kvm_vgic_finalize_idregs()`.
- ID registers: `kvm_finalize_sys_regs()` in `arch/arm64/kvm/sys_regs.c`
  rewrites the GIC fields at first run, clearing them when
  `irqchip_in_kernel()` is false.
- `kvm->max_vcpus`: the stale model limit keeps bounding later vCPU creation;
  see `kvm_arch_vcpu_precreate()` in `arch/arm64/kvm/arm.c`.
