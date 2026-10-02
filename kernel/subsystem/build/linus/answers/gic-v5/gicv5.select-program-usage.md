- `gicv5_spi_irq_set_type()`: takes `spi_config_lock` itself, with
  `guard(raw_spinlock)`, after the trigger type is validated; there is no
  gicv5_irs_spi_set_type() in this tree.
- `spi_config_lock`: a `raw_spinlock_t` in `struct gicv5_irs_chip_data`, one
  per IRS.
- `GICV5_IRS_PE_SELR`: the driver takes no lock around it.
- **Potentially unsafe usage**: writing a selector register and then the
  matching configuration register with no lock held.
  - Unsafe: when another context can write the same selector of the same IRS
    before the final wait ends; the configuration lands on the other object.
  - Safe: under `spi_config_lock` from the `GICV5_IRS_SPI_SELR` write to the
    wait after `GICV5_IRS_SPI_CFGR`, as `gicv5_spi_irq_set_type()` does.
  - Safe: `GICV5_IRS_PE_SELR` in `gicv5_irs_register_cpu()`, which runs only
    for the boot CPU from `gicv5_init_common()` and from the
    `CPUHP_AP_IRQ_GIC_STARTING` callback; `arch/arm64/Kconfig` does not
    select `HOTPLUG_PARALLEL`, so CPUs start one at a time, each under
    `cpus_write_lock()` in `_cpu_up()`.
- **Unsafe usage**: writing the configuration register after the wait that
  follows the selector write returned an error.
  - Safe: return before the configuration write, as
    `gicv5_spi_irq_set_type()` and `gicv5_irs_register_cpu()` do.
