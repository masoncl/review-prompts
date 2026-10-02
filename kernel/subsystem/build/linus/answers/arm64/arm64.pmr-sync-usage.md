- `ARM64_HAS_GIC_PRIO_RELAXED_SYNC`: set by `has_gic_prio_relaxed_sync()` in
  `arch/arm64/kernel/cpufeature.c` when `ARM64_HAS_GIC_PRIO_MASKING` is set and
  `ICC_CTLR_EL1_PMHE_MASK` is clear in `ICC_CTLR_EL1`.
- `pmr_sync()` with `CONFIG_ARM64_PSEUDO_NMI=y` and priority masking off: the
  capability is never set, so the `dsb sy` stays; `pmr_sync()` itself does not
  test `system_uses_irq_prio_masking()`.
- VHE `__kvm_vcpu_run()` in `arch/arm64/kvm/hyp/vhe/switch.c`: calls
  `pmr_sync()` with no `system_uses_irq_prio_masking()` guard.
- `kernel_exit` in `arch/arm64/kernel/entry.S`: does not use `pmr_sync()`; it
  open-codes `dsb sy` under
  `alternative_if_not ARM64_HAS_GIC_PRIO_RELAXED_SYNC`, after restoring PMR
  from `S_PMR`.
- `__pmr_local_irq_restore()` and `kernel_exit`: sync after every write,
  including when the restored value masks; a sync after a masking write is not
  an error.
- Writes of `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` with DAIF.I set: synced
  before guest entry in both `__kvm_vcpu_run()` variants (nVHE writes PMR
  itself, VHE relies on `local_daif_mask()`); not synced in
  `local_daif_mask()` or `kernel_entry`.
- `arm_cpuidle_save_irq_context()` in `arch/arm64/include/asm/cpuidle.h`: writes
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` with no `pmr_sync()`; `cpu_do_idle()`
  in `arch/arm64/kernel/idle.c` issues `dsb(sy)` before `wfi()`.
- nVHE `__kvm_vcpu_run()` after guest exit: writes `GIC_PRIO_IRQOFF` with no
  sync.
- `local_daif_inherit()`: not an example of a masking write; the `regs->pmr` it
  writes can be `GIC_PRIO_IRQON`.
- `gic_has_relaxed_pmr_sync()`: `drivers/irqchip/irq-gic-v3.c` prints "relaxed"
  or "forced" from it at boot.
