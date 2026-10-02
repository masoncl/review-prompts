| Job | Start reading from |
|---|---|
| Bringing up a secondary CPU | `gic_check_rdist()` runs first, at `CPUHP_BP_PREPARE_DYN`; then `gic_starting_cpu()`; both are registered in `gic_smp_init()` |
| Preparing MSIs for a device | `its_pci_msi_prepare()` or `its_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c`; each ends in `its_msi_prepare()` in `drivers/irqchip/irq-gic-v3-its.c` |
| Activating one LPI | `its_irq_domain_activate()`; it does not call `its_set_affinity()` |
| Initialising a guest's GICv3 | `vgic_set_common_attr()` on `KVM_DEV_ARM_VGIC_CTRL_INIT`, which calls `vgic_init()`; `kvm_vgic_map_resources()` and `vgic_lazy_init()` initialise only a GICv2 guest and fail with `-EBUSY` for an uninitialised GICv3; in `vgic_v3_map_resources()` the base address checks come first |
| Injecting an MSI into a guest | `kvm_set_msi()`, then `vgic_its_inject_msi()`; the irqfd fast path is `kvm_arch_set_irq_inatomic()`, then `vgic_its_inject_cached_translation()` |
| Saving the ITS tables for migration | `vgic_its_set_attr()`, then `vgic_its_ctrl()`, which calls `vgic_its_save_tables_v0()` through `struct vgic_its_abi`; `vgic_its_commit_v0()` is not on this path |
| All other jobs | names are unchanged in this tree: `gic_of_init()`, `gic_acpi_init()`, `gic_handle_irq()`, `gic_ipi_send_mask()`, `kvm_vgic_create()`, `kvm_vgic_flush_hwstate()`, `kvm_vgic_sync_hwstate()`, `kvm_vgic_inject_irq()`, `vgic_mmio_write_its_cwriter()` |
