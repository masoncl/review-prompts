- `gicv5_iri_irq_get_irqchip_state()`: `gic_insn(cdrcfg, CDRCFG)`, `isb()`,
  then the read of `SYS_ICC_ICSR_EL1`; there is no `gsb_sys()`.
- KVM keeps one copy, the guest's, in `vgic_icsr` of
  `struct vgic_v5_cpu_if`; nothing saves or restores the host's value.
- `__vgic_v5_save_state()` and `__vgic_v5_restore_state()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` do the save and restore.
- After a GICv5 guest has run on a CPU, `SYS_ICC_ICSR_EL1` there holds the
  guest's value, until the next CDRCFG.
- **Unsafe usage**: issuing CDRCFG and reading `SYS_ICC_ICSR_EL1` while
  preemptible; a GICv5 vCPU that enters the guest in between overwrites the
  register in `__vgic_v5_restore_state()`.
  - Safe: with `desc->lock` held and IRQs off, as both core paths to the
    callback do: `irq_get_irqchip_state()` and `__synchronize_hardirq()` in
    `kernel/irq/manage.c`.
