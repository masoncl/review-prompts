- Control register name: `GICV5_IWB_CR0`, bit `GICV5_IWB_CR0_IWBEN`; there
  is no IWB_CR definition.
- `GICV5_IWB_CR0`: read only; the driver never writes it, so it never
  enables the bridge.
- `GICV5_IWB_CR0_IWBEN` clear: `gicv5_iwb_init_bases()` returns `-EINVAL`,
  not `-ENODEV`, before any register is written.
- MSI parent: firmware must describe one (`msi-parent` on DT, an IORT IWB
  node on ACPI) so that `dev->msi.domain` is set;
  `gicv5_iwb_create_device_domain()` otherwise hits `WARN_ON_ONCE()` and
  the probe returns `-ENOMEM`.
- Wire count: `GICV5_IWB_IDR0_IW_RANGE` + 1 is `nr_regs`; the wire count is
  `nr_regs` * 32; nothing from DT or ACPI overrides it.
- Wire disable at probe: the driver writes 0 to every `GICV5_IWB_WENABLER`
  register; it does not rely on the reset state.
- Wait at probe: `gicv5_iwb_wait_for_wenabler()` follows those writes, and
  here a timeout fails the probe with the error it returned.
- Registers touched by the driver: `GICV5_IWB_IDR0`, `GICV5_IWB_CR0`,
  `GICV5_IWB_WENABLE_STATUSR`, `GICV5_IWB_WENABLER`, `GICV5_IWB_WTMR`.
- Wire domain assignment: no register for it is defined in this tree (there
  is no IWB_WDOMAINR); `GICV5_IWB_IDR0_INT_DOMS` is defined and unused.
- MMIO mapping: `platform_get_resource()` then `devm_ioremap()`, not
  `devm_platform_ioremap_resource()`; the region is not requested, and a
  missing resource returns `-EINVAL`.
- ACPI match: _HID `ARMH0003` in `iwb_acpi_match`.
- `acpi_device_clear_deps()`: called only after a successful probe;
  `drivers/acpi/scan.c` lists `ARMH0003` in `acpi_honor_dep_ids`, so ACPI
  consumers of an IWB wire are not enumerated until this call.
- Source of that dependency: `acpi_irq_add_auto_dep()` in
  `drivers/acpi/irq.c`, which asks `gic_v5_get_gsi_handle()` for the bridge
  behind each GSI of a consumer.
