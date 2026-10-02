- Instruction operand fields: the per-instruction type and ID masks, for
  example `GICV5_GIC_CDAFF_TYPE_MASK` and `GICV5_GIC_CDAFF_ID_MASK`, are in
  `arch/arm64/include/asm/sysreg.h`, not in
  `include/linux/irqchip/arm-gic-v5.h`.
- Host `hwirq`: always the bare ID in the PPI, SPI and LPI domains; each
  helper adds the type with `FIELD_PREP()` when it builds an operand, for
  example `gicv5_iri_irq_write_pending_state()`.
- `GIC CDEOI`: takes no ID; `gicv5_handle_irq()` issues `gic_insn(0, CDEOI)`.
  `GIC CDDI` in `gicv5_hwirq_eoi()` carries type and ID.
- Host places that hold a typed ID: the `GICR CDIA` result, split in
  `handle_irq_per_domain()`; and `param[0]` of an ACPI fwspec, split in
  `gicv5_irq_domain_translate()` and the two `select` callbacks.
- ACPI GSI with `GICV5_GSI_IC_TYPE` equal to `GICV5_GSI_IWB_TYPE`: not a typed
  interrupt ID; bits 28:0 hold IWB frame and wire, see
  `gic_v5_get_gsi_domain_id()`.
- KVM helpers that build and take apart a typed ID, for example
  `vgic_v5_make_ppi()` and `vgic_v5_get_hwirq_id()`: defined in
  `include/kvm/arm_vgic.h`; see "KVM interrupt ID helpers".
- KVM `intid` of `struct vgic_irq`: typed on a GICv5 VM, set by
  `vgic_v5_setup_private_irq()`; `__irq_is_ppi()`, `__irq_is_spi()` and
  `__irq_is_lpi()` read the type field.
- `kvm_vm_ioctl_irq_line()`: userspace passes a bare number; the function
  range-checks a PPI number bare and makes no check on an SPI number, then
  converts with `vgic_v5_make_ppi()` or `vgic_v5_make_spi()` before
  `kvm_vgic_inject_irq()`.
- **Unsafe usage**: passing a bare PPI number to `vgic_get_vcpu_irq()` on a
  GICv5 VM.
  - Unsafe: type field 0 fails `__irq_is_ppi()`, the call falls through to
    `vgic_get_irq()`, which returns `NULL` for a GICv5 VM.
  - Safe: wrap the loop index with `vgic_v5_make_ppi()`, as
    `vgic_v5_flush_ppi_state()` does.
- **Unsafe usage**: using a typed KVM `intid` as a bit or array index.
  - Unsafe: the type bits put the index far outside a
    `VGIC_V5_NR_PRIVATE_IRQS` bitmap.
  - Safe: take `vgic_v5_get_hwirq_id()` first, as `vgic_v5_set_ppi_dvi()`
    does; `vgic_get_vcpu_irq()` does the same before indexing `private_irqs`.
