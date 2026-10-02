- `ICH_HCR_EL2_TDIR` in `vgic_hcr`: set by `vgic_v3_configure_hcr()` when any
  of these holds, whatever the guest's EOImode:
  - host lacks `ARM64_HAS_ICH_HCR_EL2_TDIR`;
  - `irqs_active_outside_lrs()`;
  - `active_spis` is non-zero.
- With `vgic_v3_cpuif_trap` enabled, `__vgic_v3_perform_cpuif_access()`
  handles the trapped write first:
  - `ICH_HCR_EL2_TDIR` set in `vgic_hcr`: `___vgic_v3_write_dir()` finishes
    at hyp for EOImode 0, an LPI, or an INTID active in this vCPU's LRs;
    anything else exits to `access_gic_dir()` in `arch/arm64/kvm/sys_regs.c`;
  - bit clear in `vgic_hcr`: `__vgic_v3_write_dir()` finishes at hyp, and
    bumps EOIcount in the case that would exit with the bit set.
- `active_spis` (`atomic_t` in `struct vgic_dist`): not an exact count of
  active SPIs.
  - Incremented in `vgic_queue_irq_unlock()` per SPI queued, only when
    `vgic_model_needs_bcst_kick()`.
  - Decremented only in `vgic_v3_fold_lr()`, with `atomic_dec_if_positive()`,
    on the irqfd condition in "Reading the list registers back".
  - Readers test it against zero only.
- `vgic_v3_deactivate()` returns at once for EOImode 0 in `vgic_vmcr`, or an
  INTID at or above `nr_spis + VGIC_NR_PRIVATE_IRQS`.

| Interrupt | Physical deactivation |
|---|---|
| `irq->vcpu` NULL | none |
| `on_lr` set | via `vgic_mmio_write_cactive()`: `vgic_irq_set_phys_active()` for `irq->hw` non-SGI |
| v2 SGI, `active_source` != CPUID | none |
| pseudo-LR has `ICH_LR_HW`, vCPU not nested | `vgic_v3_deactivate_phys()` |
| pseudo-LR has `ICH_LR_HW`, `vgic_state_is_nested()` | none |
| pseudo-LR without `ICH_LR_HW` | none by `vgic_v3_deactivate()`; fold only |
