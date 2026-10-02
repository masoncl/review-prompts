- Models take the GICv4 calls from KVM into the ITS driver to run in process
  context. `update_lpi_config()` and `update_affinity()` call
  `its_prop_update_vlpi()` and `its_get_vlpi()` with `irq->irq_lock` held, so
  `its_irq_set_vcpu_affinity()` and its callees may only spin.
- Models take `arch/arm64/kvm/vgic/vgic-v5.c` to be only the compat layer for
  GICv3 guests. For a `KVM_DEV_TYPE_ARM_VGIC_V5` VM the private interrupts
  get their INTIDs from `vgic_v5_make_ppi()`, and `kvm_vgic_sync_hwstate()`
  skips `vgic_prune_ap_list()`.
- Models take `kvm_vgic_global_state.type` to be `VGIC_V3` whenever a GICv3
  guest can run. `vgic_v5_probe()` sets it to `VGIC_V5` and enables the
  `gicv3_cpuif` static key under `ARM64_HAS_GICV5_LEGACY`; the host test is
  `vgic_host_has_gicv3()`.
- Models take `irq_is_ppi()`, `irq_is_sgi()`, `irq_is_spi()`, `irq_is_lpi()`
  and `irq_is_private()` to take an INTID only. In `include/kvm/arm_vgic.h`
  they take the `struct kvm *` first and decode by `vgic_model`.
- Models take every field of `struct its_vpe` to be valid on any GICv4. In
  `include/linux/irqchip/arm-gic-v4.h` a union overlays the GICv4.0 fields
  `vpe_proxy_event` and `idai` with the GICv4.1 fields `fwnode`,
  `sgi_domain` and `sgi_config`.
- Models take partitioned PPIs to be backed by irq-partition-percpu.c. There
  is no such file in this tree.
- Models take `its_msi_teardown()` to be one function.
  `drivers/irqchip/irq-gic-its-msi-parent.c` has its own static
  `its_msi_teardown()`, separate from the one in
  `drivers/irqchip/irq-gic-v3-its.c`.
- Models know one vGIC debugfs file. `vgic_its_debug_init()` adds one per
  vITS, and `vgic_its_debug_start()` takes `its->its_lock`, released only in
  `vgic_its_debug_stop()`.
- Models expect `kzalloc()` and `kcalloc()` in
  `drivers/irqchip/irq-gic-v3-its.c` and under `arch/arm64/kvm/vgic/`. Most
  allocations there use `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`
  from `include/linux/slab.h`.
