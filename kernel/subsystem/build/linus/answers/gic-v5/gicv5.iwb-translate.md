- ACPI `param[0]`: the whole GSI, not a wire number; the wire is
  `FIELD_GET(GICV5_GSI_IWB_WIRE, fwspec->param[0])`.
- GSI layout, from `include/linux/irqchip/arm-gic-v5.h`:

| Field | Bits | Meaning |
|---|---|---|
| `GICV5_GSI_IC_TYPE` | [31:29] | `GICV5_GSI_IWB_TYPE` (0x7) marks an IWB |
| `GICV5_GSI_IWB_FRAME_ID` | [28:16] | which bridge |
| `GICV5_GSI_IWB_WIRE` | [15:0] | wire on that bridge |

- IWB recognition: decided by `GICV5_GSI_IC_TYPE` alone; a frame ID of 0 is
  a valid bridge, not a marker for a non-IWB interrupt.
- `gic_v5_get_gsi_domain_id()`: returns a `struct fwnode_handle *`, not an
  ID; for an IWB it is the fwnode of the bridge's ACPI device, from
  `iort_iwb_handle_fwnode()`.
- `iort_iwb_handle()`: called by `gic_v5_get_gsi_handle()`, the second
  callback passed to `acpi_set_irq_model()`; it returns the `acpi_handle`
  used for probe dependencies.
- Frame ID lookup: through the IORT only; `iort_match_iwb_callback()`
  compares the frame ID with `iwb_index` in `struct acpi_iort_iwb`, and
  `device_name` there names the ACPI device. The MADT has no IWB entry.
- Range check: `gicv5_iwb_irq_domain_translate()` has none, and the domain
  size does not bound the wire either.
- First range check: `gicv5_its_alloc_eventid()` returns `-EINVAL` when the
  wire is >= `num_events`, which is the wire count rounded up to a power of
  two.
- Wires between the wire count and `num_events`: get a mapping; when a
  trigger type is set they fail later, at the `nr_regs` check in
  `gicv5_iwb_set_type()`.
- Trigger validation: translate only masks `param[1]` with
  `IRQ_TYPE_SENSE_MASK`; unsupported types are refused by
  `gicv5_iwb_set_type()`.
- Other fwnode types: translate has no branch for them and returns 0 with
  `*hwirq` and `*type` unwritten; `-EINVAL` is returned only for
  `param_count` < 2.
- Why that is not reached: the domain's fwnode is the bridge device's
  fwnode (`MSI_FLAG_USE_DEV_FWNODE`), which is an OF node or an ACPI device
  node.
