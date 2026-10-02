- `allocate_lpi_tables()`: tests `GICR_CTLR_ENABLE_LPIS` on the boot CPU's
  redistributor itself; `enabled_lpis_allowed()` only reads the
  `GICR_PROPBASER` address and passes it to `gic_check_reserved_range()`. It
  checks no attributes and no `GICR_TYPER` bit.
- Range checked by `enabled_lpis_allowed()`: 64K. `lpi_id_bits` is still 0
  at that point, so `LPI_PROPBASE_SZ` evaluates to `SZ_64K` whatever size
  the previous kernel used.
- On adoption `allocate_lpi_tables()` sets
  `RDIST_FLAGS_RD_TABLES_PREALLOCATED` and
  `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING`.
- Per CPU, `its_cpu_init_lpis()` adopts only when the global flag is set and
  that redistributor has `GICR_CTLR_ENABLE_LPIS`; a redistributor with LPIs
  off is programmed with the adopted property table and its newly allocated
  pending table.
- `GICR_PROPBASER` differing from `gic_rdists->prop_table_pa`: `WARN_ON()`
  and `add_taint()` only; the CPU still sets
  `RD_LOCAL_PENDTABLE_PREALLOCATED` and skips programming.
- `redist_disable_lpis()` first returns `-ENXIO` when `GICR_TYPER_PLPIS` is
  clear.
- `redist_disable_lpis()` returns 0 and changes nothing when
  `GICR_CTLR_ENABLE_LPIS` is clear, when `RD_LOCAL_LPI_ENABLED` is set, or
  when `RDIST_FLAGS_RD_TABLES_PREALLOCATED` is set.
- `redist_disable_lpis()` damage control: the warning and
  `add_taint(TAINT_CRAP, LOCKDEP_STILL_OK)` come before the attempt to clear
  the bit, so they happen even when the clear succeeds.
- `its_cpu_init()` return value: ignored by both callers, `gic_init_bases()`
  and `gic_starting_cpu()`. On an error the CPU still comes up, with
  `its_cpu_init_lpis()` and `its_cpu_init_collections()` skipped.
