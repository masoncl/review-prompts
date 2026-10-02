- Chip selection: `its_vpe_irq_domain_alloc()` picks `its_vpe_4_1_irq_chip`
  when `gic_rdists->has_rvpeid`, else `its_vpe_irq_chip`.
- The test for GICv4.1 differs by file: `gic_rdists->has_rvpeid` picks the
  chip in `drivers/irqchip/irq-gic-v3-its.c`, `has_v4_1()` is used in
  `drivers/irqchip/irq-gic-v4.c`, and `kvm_vgic_global_state.has_gicv4_1` in
  KVM.
- `its_vpe_4_1_mask_irq()` and `its_vpe_4_1_unmask_irq()`: real operations,
  `lpi_write_config()` then `its_send_invdb()`; on GICv4.1
  `its_make_vpe_resident()`, `its_make_vpe_non_resident()` and
  `vgic_v4_doorbell_handler()` skip their `enable_irq()` and
  `disable_irq_nosync()` calls.
- GICv4.1 enable: `vgic_v4_init()` removes `IRQ_NOAUTOEN` from
  `DB_IRQ_FLAGS`, so `request_irq()` enables the doorbell;
  `its_vpe_4_1_deschedule()` sets `GICR_VPENDBASER_4_1_DB` only with
  `req_db`.
- GICv4.0 enable: the `enable_irq()` loop in `its_make_vpe_non_resident()`
  runs only when `db` is true; with `db` false the doorbell stays disabled.
- GICv4.0 disable: `disable_irq_nosync()` in `its_make_vpe_resident()`, and
  in `vgic_v4_doorbell_handler()` when the interrupt is not already disabled.
- `pending_last` at deschedule: assigned, not ORed; on GICv4.1 with `req_db`
  the write to the register and the assignment are both inside
  `vpe->vpe_lock`, which the handler also takes.
