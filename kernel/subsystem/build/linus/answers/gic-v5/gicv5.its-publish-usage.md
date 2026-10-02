- `gicv5_its_dcache_clean()` with `ITS_FLAGS_NON_COHERENT`: calls
  `dcache_clean_inval_poc()`, a clean and invalidate, not a clean alone.
- `gicv5_its_map_event()` and `gicv5_its_unmap_event()`: discard the result
  of `gicv5_its_itt_cache_inv()`; `gicv5_its_map_event()` returns 0 on a
  timeout and leaves the ITTE valid.
- `gicv5_its_device_register()`: the only caller that acts on a failed
  invalidate; it writes the DTE back to 0 and frees the ITT.
- Locks for callers: `dev_alloc_lock` for a DTE, no driver lock for an
  ITTE; see "ITS locking".
- **Potentially unsafe usage**: changing an entry with no invalidate after
  it.
  - Unsafe: when the ITS can already reach the entry, i.e. an L2 or linear
    DTE once `GICV5_ITS_DT_BASER` is programmed, or an L2 or linear ITTE of
    a device whose DTE is valid; the ITS may keep using its cached copy.
  - Safe: L1 ITTEs in `gicv5_its_create_itt_two_level()`; the ITT is not
    reachable until `gicv5_its_device_register()` writes the DTE, and that
    write is followed by `gicv5_its_device_cache_inv()`.
- **Potentially unsafe usage**: storing an entry without
  `its_write_table_entry()`.
  - Unsafe: when the ITS can already reach the table; nothing cleans the
    line for `ITS_FLAGS_NON_COHERENT` and nothing issues `dsb(ishst)`
    otherwise.
  - Safe: filling a table before it is handed to the ITS, then one
    `gicv5_its_dcache_clean()` over the whole table, as
    `gicv5_its_alloc_devtab_two_level()` does before it writes
    `GICV5_ITS_DT_BASER`.
- **Unsafe usage**: setting a parent entry valid before the table it points
  to has been through `gicv5_its_dcache_clean()`.
  - Unsafe: the zero fill from `kcalloc()` may still sit in the CPU cache,
    so a non-coherent ITS reads stale memory as entries.
  - Safe: `gicv5_its_create_itt_two_level()` cleans each L2 ITT before it
    stores the L1 entry that points to it.
  - Safe: `gicv5_its_create_itt_linear()` cleans the ITT before
    `gicv5_its_device_register()` writes the DTE.
