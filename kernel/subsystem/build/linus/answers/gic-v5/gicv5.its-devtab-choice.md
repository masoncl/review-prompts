- Linear is chosen only when `GICV5_ITS_IDR1_DT_LEVELS` is clear or the device
  ID bits are below the L2 bits; see `gicv5_its_l2sz_two_level()`.
- Device ID bits equal to the L2 bits: two-level, with a one-entry L1 table.
- No L2 size advertised in `GICV5_ITS_IDR1`: does not force linear;
  `gicv5_its_l2sz_two_level()` falls back to `GICV5_ITS_DT_ITT_CFGR_L2SZ_4k`.
- Cap: there is no driver macro; the limit is `KMALLOC_MAX_SIZE`.

| Structure | What is held to `KMALLOC_MAX_SIZE` | Resulting device ID bits |
|---|---|---|
| linear, `gicv5_its_alloc_devtab_linear()` | whole table | `ilog2(KMALLOC_MAX_SIZE/sizeof(__le64))` |
| two-level, `gicv5_its_alloc_devtab_two_level()` | L1 table only | that value plus the L2 bits |

- Capped value: written to `GICV5_ITS_DT_CFGR` and kept in
  `its->devtab_cfgr.cfgr`; `gicv5_its_device_register()` checks device IDs
  against it.
- `gicv5_its_deinit_devtab()`, two-level table: frees the L1 table and the
  `l2ptrs` array, not the L2 tables; its only caller is the failure path of
  `gicv5_its_init_bases()`.
