| Job | Start reading from | Easy to miss |
|---|---|---|
| Probe from ACPI | `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c`, then `gicv5_irs_acpi_probe()` | static; `drivers/irqchip/irq-gic-v3.c` has a static function of the same name |
| Probe the ITS, DT or ACPI | `gicv5_irs_its_probe()` in `drivers/irqchip/irq-gic-v5-irs.c` | it picks `gicv5_its_of_probe()` or `gicv5_its_acpi_probe()` |
| Probe an IWB | `gicv5_iwb_device_probe()` in `drivers/irqchip/irq-gic-v5-iwb.c` | a platform driver, for DT and ACPI alike |
| Bring up a CPU's interface | `gicv5_starting_cpu()` | the hotplug callback is this, not `gicv5_cpu_enable_interrupts()`; `gicv5_init_common()` calls it directly for the boot CPU |
| Allocate an LPI | `gicv5_irq_lpi_domain_alloc()` in `drivers/irqchip/irq-gic-v5.c` | there is no gicv5_alloc_lpi() or gicv5_free_lpi(); static `alloc_lpi()` and `release_lpi()` do that; child domains use `irq_domain_alloc_irqs_parent()` |
| Configure an SPI's trigger | `gicv5_spi_irq_set_type()` | defined in `drivers/irqchip/irq-gic-v5-irs.c`, installed in `gicv5_spi_irq_chip` in `drivers/irqchip/irq-gic-v5.c`; there is no gicv5_irs_spi_set_type() |
| Register a device with an ITS | `gicv5_its_msi_prepare()`, then `gicv5_its_alloc_device()`, then `gicv5_its_device_register()` | reached from `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c` |
| Map an event to an LPI | `gicv5_its_irq_domain_activate()`, then `gicv5_its_map_event()` | done at activate, not in `gicv5_its_irq_domain_alloc()` |
| Enable an IWB wire | `gicv5_iwb_irq_enable()`, then `gicv5_iwb_enable_wire()` | it is the `.irq_enable` callback; `.irq_unmask` is `irq_chip_unmask_parent()`; there is no gicv5_iwb_irq_domain_alloc() |
