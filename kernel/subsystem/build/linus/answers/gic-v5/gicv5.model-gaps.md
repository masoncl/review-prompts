- Models take the ITS and IPI domains to free LPI numbers themselves. Both
  free callbacks call `irq_domain_free_irqs_parent()`, which reaches
  `release_lpi()` in `gicv5_irq_lpi_domain_free()`; a child that releases an
  LPI itself frees it twice.
- Models take a GICv5 vCPU to have 128 private interrupts. 128 is the host
  driver's `PPI_NR` in `drivers/irqchip/irq-gic-v5.c`; for the vCPU count see
  `VGIC_V5_NR_PRIVATE_IRQS`.
- Models take an IRS to stay enabled once probed. When `gicv5_init_common()`
  fails, `gicv5_irs_remove()` disables every IRS and also calls
  `gicv5_deinit_lpis()`.
- Models take a guest to see `ID_AA64PFR2_EL1.GCIE` only once a GICv5 device
  exists. On a GICv5 host `sanitise_id_aa64pfr2_el1()` presents it as IMP with
  no test for a vgic device; `kvm_vgic_create()` and `kvm_finalize_sys_regs()`
  fix it up, and the latter clears it when there is no in-kernel irqchip.
- Models do not know that a GICv5 guest changes the WFI trap choice. Under the
  default policy `kvm_vcpu_should_clear_twi()` in `arch/arm64/kvm/arm.c`
  returns `single_task_running()` for it, with no vLPI or vSGI test.
- Models take `acpi_set_irq_model()` to have two parameters. The third, a
  GSI-to-`acpi_handle` callback, is NULL in the GICv3 driver.
- Models expect `kzalloc(sizeof(*p), GFP_KERNEL)`. The GICv5 drivers allocate
  typed objects with `kzalloc_obj()` and `kzalloc_objs()` from
  `include/linux/slab.h`; an omitted flags argument means `GFP_KERNEL`.
