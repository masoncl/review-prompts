- `vgic_is_v5()`: tested first; a GICv5 VM returns
  `vgic_v5_has_pending_ppi()` and none of the checks below run.
- `its_vpe.pending_last`: read directly, with no
  `vgic_supports_direct_irqs()` test and no helper call.
- `its_vpe_4_1_deschedule()` without a doorbell request: sets `pending_last`
  to true unconditionally, so true does not imply a pending VLPI.
- Nothing under `arch/arm64/kvm` clears `pending_last`.
- Per-interrupt test: `irq_is_pending(irq) && irq->enabled && !irq->active &&
  irq->priority < vmcr.pmr`; an active interrupt never counts.
- Group enables: decoded by `vgic_get_vmcr()` but not used; only `pmr` is.
- `pmr` freshness: `vgic_vmcr` is rewritten at every guest exit (see "The
  virtual machine control register"); `kvm_vgic_put()` in `kvm_vcpu_wfi()`
  does not read the VMCR on a GICv3 host.
- Callers besides `kvm_arch_vcpu_runnable()`: `vgic_kick_vcpus()` calls it for
  every vCPU of the VM, running or not, and only kicks on true;
  `kvm_vgic_flush_hwstate()` calls it in nested state.
