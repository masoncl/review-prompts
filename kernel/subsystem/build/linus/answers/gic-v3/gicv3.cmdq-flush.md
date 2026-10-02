- `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` set: `its_flush_cmd()` calls
  `gic_flush_dcache_to_poc()` on the block; clear: `dsb(ishst)` only.
- The flag comes only from the `GITS_CBASER` write and read-back in
  `its_probe_one()`; `GITS_TYPER` plays no part.
- `RDIST_FLAGS_FORCE_NON_SHAREABLE` is not tested for the command queue.
- `ITS_FLAGS_FORCE_NON_SHAREABLE` is set before the comparison of the
  `GITS_CBASER` read-back with the value written (what it does to that
  comparison is in "Non-coherent GICs"), either by an `its_quirks` entry or
  by `gic_acpi_parse_madt_its()`.
  - `its_enable_quirks()` runs first in `its_probe_one()`; the entries are
    `its_enable_rk3588001()` and the "dma-noncoherent" property.
  - `gic_acpi_parse_madt_its()` sets it from `ACPI_MADT_ITS_NON_COHERENT`,
    only when `acpi_get_madt_revision() >= 7`, before it calls
    `its_probe_one()`.
