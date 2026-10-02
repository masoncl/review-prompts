- Model value: `gic_acpi_init()` registers `ACPI_IRQ_MODEL_GIC_V5`, not
  `ACPI_IRQ_MODEL_GIC`.
- Tests of `acpi_irq_model == ACPI_IRQ_MODEL_GIC` do not match on GICv5; for
  example `acpi_irq_create_hierarchy()` in `drivers/acpi/irq.c` returns NULL.
- `acpi_set_irq_model()`: takes three arguments here; GICv5 passes
  `gic_v5_get_gsi_domain_id()` (GSI to domain fwnode) and
  `gic_v5_get_gsi_handle()` (GSI to the `acpi_handle` it depends on).
- `IRQCHIP_ACPI_DECLARE()` validate callback: `acpi_validate_gic_table()`, not
  NULL; `gic_acpi_init()` runs only for an IRS entry whose `version` equals
  `ACPI_MADT_GIC_VERSION_V5`.
- MADT walks, all with `acpi_table_parse_madt()`:

  | For | MADT type | Callback | Started by |
  |---|---|---|---|
  | IRS | `ACPI_MADT_TYPE_GICV5_IRS` | `gic_acpi_parse_madt_irs()` | `gicv5_irs_acpi_probe()` |
  | CPU IAFFID | `ACPI_MADT_TYPE_GENERIC_INTERRUPT` | `gic_acpi_parse_iaffid()` | `gicv5_irs_acpi_init_affinity()` |
  | ITS config frame | `ACPI_MADT_TYPE_GICV5_ITS` | `gic_acpi_parse_madt_its()` | `gicv5_its_acpi_probe()` |
  | ITS translate frame | `ACPI_MADT_TYPE_GICV5_ITS_TRANSLATE` | `gic_acpi_parse_madt_its_translate()` | `gic_acpi_parse_madt_its()` |

- Translate-frame walk: nested in the ITS callback, so it runs once per ITS.
- `gic_acpi_parse_iaffid()` skips a GICC entry, returning 0, unless all hold:
  - `flags` has `ACPI_MADT_ENABLED` or `ACPI_MADT_GICC_ONLINE_CAPABLE`;
  - `irs_id` equals the `irs_id` of the IRS being probed;
  - `get_logical_index()` finds `arm_mpidr`;
  - `iaffid` fits the width read from `GICV5_IRS_IDR1`.
- ITS probe: `gicv5_its_acpi_probe()` is called from `gicv5_irs_its_probe()`
  at the end of `gicv5_init_common()`, before `acpi_set_irq_model()`.
- ITS frame match: `linked_translator_id` of the frame equals `translator_id`
  of the ITS.
- ITS frame fwnode: one per frame, from `irq_domain_alloc_parented_fwnode()`
  with the ITS fwnode as parent, registered with
  `iort_register_domain_token()` under `translate_frame_id`.
- ITS domain: one per ITS, on the ITS fwnode, with
  `IRQ_DOMAIN_FLAG_FWNODE_PARENT`; `msi_lib_irq_domain_select()` matches the
  parent of the frame fwnode that IORT returns.
- GSI layout, in `include/linux/irqchip/arm-gic-v5.h`:
  - bits 31:29 are `GICV5_GSI_IC_TYPE`, the same bits as `GICV5_HWIRQ_TYPE`;
  - type `GICV5_GSI_IWB_TYPE` (0x7): `GICV5_GSI_IWB_FRAME_ID` is bits 28:16,
    `GICV5_GSI_IWB_WIRE` is bits 15:0;
  - any other type: `GICV5_HWIRQ_ID` is bits 23:0.
- GIC fwnode: one for the whole GIC, `gsi_domain_handle`, allocated from the
  first IRS entry; `gic_v5_get_gsi_domain_id()` returns it for every non-IWB
  GSI.
- PPI and SPI domains: both sit on that fwnode with `DOMAIN_BUS_WIRED`;
  `gicv5_irq_ppi_domain_select()` and `gicv5_irq_spi_domain_select()` choose
  by the type bits of `fwspec->param[0]`.
- SPI domain: one global domain, not one per IRS;
  `gicv5_irs_lookup_by_spi_id()` only picks the chip data in
  `gicv5_irq_spi_domain_alloc()`.
- A GSI whose type is not PPI, SPI or IWB: `gicv5_irq_domain_translate()`
  returns `-EINVAL`, so no mapping is created.
- IWB domain: exists only after `gicv5_iwb_device_probe()` in
  `drivers/irqchip/irq-gic-v5-iwb.c`; before that `acpi_irq_get()` returns
  `-EPROBE_DEFER`, and the probe ends with `acpi_device_clear_deps()`.
