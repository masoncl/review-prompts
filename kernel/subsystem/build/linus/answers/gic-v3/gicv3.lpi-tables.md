- Pending tables: `allocate_lpi_tables()` allocates one for every possible
  CPU in one loop, from `its_init()` on the boot CPU; no CPU allocates its
  own later.
- Extra allocation flag: `its_alloc_pages()` calls `its_alloc_pages_node()`,
  which ORs `gfp_flags_quirk` into the caller's flags; see "Allocating memory
  for the GIC".
- Fill value of the property table: `lpi_prop_prio | LPI_PROP_GROUP1`; the
  driver does not use `LPI_PROP_DEFAULT_PRIO`.
- Property table reservation: done in `its_setup_lpi_prop_table()`, and only
  on the branch that allocates the table. `its_cpu_memreserve_lpi()` deals
  with the pending table only.
- Adopted tables (`RDIST_FLAGS_RD_TABLES_PREALLOCATED`,
  `RD_LOCAL_PENDTABLE_PREALLOCATED`): this kernel makes no
  `gic_reserve_range()` call for them.
- `gic_reserve_range()`: tests `efi_enabled(EFI_CONFIG_TABLES)` at run time,
  not a configuration symbol; a failed reservation is only a `WARN_ON()` at
  both call sites.
- `its_lpi_memreserve_init()`: not an initcall; `gic_init_bases()` calls it
  after `its_cpu_init()`. It registers `its_cpu_memreserve_lpi()` only when
  `efi_enabled(EFI_CONFIG_TABLES)` is true and `its_nodes` is not empty;
  otherwise the callback never runs.
