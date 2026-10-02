- Flags and setters:

| Flag | Set by |
|---|---|
| `ITS_FLAGS_FORCE_NON_SHAREABLE` | `its_set_non_coherent()`, `its_enable_rk3588001()`, `gic_acpi_parse_madt_its()` |
| `RDIST_FLAGS_FORCE_NON_SHAREABLE` | `rd_set_non_coherent()`, `its_enable_rk3588001()`, `gic_acpi_parse_madt_redist()`, `gic_acpi_parse_madt_gicc()` |
| `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` | `its_probe_one()` |
| `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` | `its_cpu_init_lpis()`, `allocate_lpi_tables()` |

- "dma-noncoherent": a `.property` entry in `its_quirks` and `gic_quirks`,
  run by `gic_enable_of_quirks()`; `gic_of_init()` does not read it
  directly.
- ACPI setters: act only when `acpi_get_madt_revision() >= 7`.
- `allocate_lpi_tables()`: sets `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING`
  together with `RDIST_FLAGS_RD_TABLES_PREALLOCATED`; `its_cpu_init_lpis()`
  then skips programming `GICR_PROPBASER` on a redistributor that has
  `GICR_CTLR_ENABLE_LPIS` set.
- The two derived flags: set on any shareability mismatch with what was
  written, not only on a read-back of 0; the rewrite with nC happens only
  on 0.
- `GITS_CBASER`, `GICR_PROPBASER`, `GICR_PENDBASER` under a force flag:
  written as inner-shareable first, then the read-back shareability is
  masked to 0, which forces the nC rewrite.
- `GITS_BASER` under `ITS_FLAGS_FORCE_NON_SHAREABLE`: no masking;
  `its_alloc_tables()` starts from `shr` 0 and `GITS_BASER_nC`.
- `GICR_PENDBASER` mismatch: sets no flag.
- `its_cpu_init_lpis()`: flushes no table; `gic_reset_prop_table()` and
  `its_allocate_pending_table()` flush at allocation, unconditionally.
- Write sites never test a force flag; each tests a derived value or
  flushes always:

| Object written | Test for the flush |
|---|---|
| command | `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` |
| LPI or vLPI config byte | `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` |
| `GITS_BASER` table | the `shr` about to be written, in `its_setup_baser()` |
| `GITS_BASER` level-2 page, level-1 entry | `GITS_BASER_SHAREABILITY_MASK` in `baser->val` |
| redistributor vPE level-2 page, level-1 entry | `GICR_VPROPBASER_SHAREABILITY_MASK` read from `GICR_VPROPBASER` |
| property table, pending table, ITT at allocation | none, always flushed |
