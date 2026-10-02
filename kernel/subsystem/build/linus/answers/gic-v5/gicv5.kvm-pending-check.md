- Mask helper: `vgic_v5_get_effective_priority_mask()` in
  `arch/arm64/kvm/vgic/vgic-v5.c`.
- Enable bit: if `FEAT_GCIE_ICH_VMCR_EL2_EN` is clear in the saved
  `vgic_vmcr`, the mask is 0.
- Mask of 0: `vgic_v5_has_pending_ppi()` returns false before it looks at any
  PPI.
- Mask otherwise: the minimum of VPMR plus one and the trailing-zero count of
  `vgic_apr` (32 when no bit is set).
- Comparison: `irq->enabled && irq->priority < mask`. With no active
  priority, a priority equal to VPMR passes; a priority equal to the highest
  active priority never does.
- `irq->active`: not tested.
- Hardware-mapped PPI: `irq->hw` selects `vgic_get_phys_line_level()`;
  `pending_latch`, `line_level` and the saved pending register are not used.
- `vgic_get_phys_line_level()`: calls `irq->ops->get_input_level()` when set,
  and `irq_get_irqchip_state()` on `irq->host_irq` only otherwise.
- Timers: the hook is `kvm_arch_timer_get_input_level()`. It takes only the
  INTID and evaluates `kvm_timer_pending()` for the timer of
  `kvm_get_running_vcpu()`, not of the `vcpu` passed to
  `vgic_v5_has_pending_ppi()`.
- Age of the inputs: `vgic_vmcr` is from the last exit, `vgic_apr` from the
  last put, `irq->priority` from the last put made in WFI.
