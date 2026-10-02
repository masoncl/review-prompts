- Checks in `gicv5_its_device_register()`, in order, besides the two
  `-ENOMEM` allocations:

| Check | Error |
|---|---|
| `device_id >= BIT(device_id_bits)`, bits from saved `devtab_cfgr.cfgr` | `-EINVAL` |
| device table entry has `GICV5_DTL2E_VALID` | `-EBUSY` |
| `event_id_bits` above `GICV5_ITS_IDR2_EVENTID_BITS` | `-EINVAL` |
| `gicv5_its_create_itt_two_level()` with `event_id_bits` equal to L2 bits | `-EINVAL` |
| `gicv5_its_device_cache_inv()` times out | `-ETIMEDOUT` |

- L2 device table: allocated by `gicv5_its_devtab_get_dte_ref()` before the
  `-EBUSY` and event ID checks, so those returns leave a new L2 table in
  place.
- Device table entry: all fields and `GICV5_DTL2E_VALID` go in one
  `its_write_table_entry()`; there is no separate write of the valid bit and
  no barrier between fields.
- Final invalidation fails: the entry is written to 0 with
  `its_write_table_entry()`, `gicv5_its_free_itt()` runs, the error is
  returned.
