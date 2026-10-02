- ITS domain `hwirq`: 64-bit, DeviceID in `GICV5_ITS_HWIRQ_DEVICE_ID`, EventID
  in `GICV5_ITS_HWIRQ_EVENT_ID`; it is not the LPI. The LPI is
  `d->parent_data->hwirq`, read in `gicv5_its_irq_domain_activate()`.
- IPI domain `hwirq`: the index inside the one allocation, set in
  `gicv5_irq_ipi_domain_alloc()`; the LPI is in the parent `irq_data`.
- IWB domain `hwirq`: the wire number; `gicv5_iwb_domain_set_desc()` copies it
  to `alloc_info->hwirq`, and `MSI_ALLOC_FLAGS_FIXED_MSG_DATA` makes
  `gicv5_its_alloc_eventid()` use it as the EventID.
- LPI domain `hwirq`: taken from `alloc_lpi()` inside
  `gicv5_irq_lpi_domain_alloc()`; the `arg` pointer is not used, and
  `gicv5_its_irq_domain_alloc()` passes `NULL` to the parent.
- Typed ID split on the host: in `handle_irq_per_domain()`;
  `gicv5_handle_irq()` only extracts `GICV5_HWIRQ_INTID`.
- ITS `hwirq` readers: only the EventID half is read back, into a `u16` in
  the domain callbacks; no code reads `GICV5_ITS_HWIRQ_DEVICE_ID` back out,
  the DeviceID comes from `struct gicv5_its_dev`.
- MSI address: `its_trans_phys_base` of `struct gicv5_its_dev`, copied from
  `info->scratchpad[1]` in `gicv5_its_msi_prepare()`;
  `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c` fill it per device.
