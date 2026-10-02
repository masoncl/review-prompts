- Global values set in `gicv5_irs_init()` under `list_empty(&irs_nodes)`:

| Register | Field | Stored in `gicv5_global_data` |
|---|---|---|
| `GICV5_IRS_IDR0` | `GICV5_IRS_IDR0_VIRT` | `virt_capable` |
| `GICV5_IRS_IDR1` | `GICV5_IRS_IDR1_PRIORITY_BITS` | `irs_pri_bits` |
| `GICV5_IRS_IDR5` | `GICV5_IRS_IDR5_SPI_RANGE` | `global_spi_count` |

- `GICV5_IRS_IDR2` IST fields: not read in `gicv5_irs_init()`; read in
  `gicv5_irs_init_ist()` from the first entry of `irs_nodes`, when
  `gicv5_irs_enable()` runs.
- Per IRS: `GICV5_IRS_IDR2_LPI` (clear gives `-ENODEV` with a `WARN()`),
  `GICV5_IRS_IDR6`, `GICV5_IRS_IDR7`, and `GICV5_IRS_IDR1_IAFFID_BITS`.
- `GICV5_IRS_IDR1_IAFFID_BITS`: read per IRS by `gicv5_irs_of_init()` and
  `gicv5_irs_acpi_init_affinity()`, although the comment in
  `gicv5_irs_init()` lists it as a global property.
- The IRS used: the first to pass the LPI test in `gicv5_irs_init()`; it is
  also the first entry of `irs_nodes`.
- An IRS that fails earlier (mapping, affinity parse) does not count, so on
  the device tree path the IRS used need not be the first child node.
- Later IRSs: no comparison with the stored values.
