- `gicv5_init_common()` in `drivers/irqchip/irq-gic-v5.c`: holds the probe
  steps that both paths share after the IRS probe; `gicv5_of_init()` and the
  ACPI entry both call it.
- ACPI entry: `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c` (the GICv3
  driver has a function of the same name); it calls
  `gicv5_irs_acpi_probe()`, and `gicv5_its_acpi_probe()` is reached through
  `gicv5_init_common()`.
- IRS probe: `gicv5_irs_init()` tests `GICV5_IRS_IDR2_LPI` on every IRS; an
  IRS that fails is dropped with a `WARN()`, and the probe returns
  `-ENODEV` only when no IRS is left on `irs_nodes`.
- Boot CPU: `gicv5_starting_cpu()` fails the probe when the CPU lacks
  `ARM64_HAS_GICV5_CPUIF` or when `gicv5_irs_register_cpu()` fails, for
  example with no valid IAFFID or no IRS recorded for that CPU.
- Several IRSes: the IST is set up on the first entry of `irs_nodes` only; SPI
  trigger config goes to the IRS found by `gicv5_irs_lookup_by_spi_id()`; a
  CPU registers with the IRS in `per_cpu_irs_data`.
- ITS device tree nodes: children of an IRS node, not of the GIC node;
  `gicv5_irs_its_probe()` calls `gicv5_its_of_probe()` once per IRS.
- IWB: not probed by the GIC driver; a platform driver
  (`gicv5_iwb_platform_driver`) bound by "arm,gic-v5-iwb" or ACPI
  "ARMH0003"; `gicv5_iwb_init_bases()` returns `ERR_PTR(-EINVAL)` when
  firmware left `GICV5_IWB_CR0_IWBEN` clear.
