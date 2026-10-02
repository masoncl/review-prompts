- **Unsafe usage**: a restore function that creates a device, event or
  collection without the device ID, event ID, collection ID and event ID
  size checks of its command handler.
  - Unsafe: `num_eventid_bits` above `VITS_TYPER_IDBITS`;
    `vgic_its_restore_itt()` passes `BIT_ULL(dev->num_eventid_bits) * ite_esz`
    to the `int size` of `scan_its_table()`.
  - Unsafe: an event ID above `VITS_MAX_EVENTID`; `vgic_its_cache_key()` packs
    the event ID into `VITS_TYPER_IDBITS` bits below the device ID.
  - Safe: `vgic_its_restore_dte()` makes the `VITS_TYPER_IDBITS` and
    `vgic_its_check_id()` tests of `vgic_its_cmd_handle_mapd()`.
  - Safe: `vgic_its_restore_ite()` calls `vgic_its_check_event_id()`, as
    `vgic_its_cmd_handle_mapi()` does.
  - Safe: `vgic_its_restore_cte()` calls `vgic_its_check_id()` and
    `kvm_get_vcpu_by_id()`, as `vgic_its_cmd_handle_mapc()` does.
- **Potentially unsafe usage**: restoring an object without looking for one
  that already has its ID.
  - Unsafe: for the collection table, which is walked entry by entry and
    carries the ID inside each entry, so two entries can name one collection.
  - Safe: `vgic_its_restore_cte()` calls `find_collection()` first and returns
    `-EEXIST`.
  - Safe: `vgic_its_restore_ite()` adds to a device that
    `vgic_its_restore_dte()` has just allocated, and `scan_its_table()` gives
    each event ID once.
- Restore-only check: the next-offset field; `vgic_its_restore_ite()` rejects
  `event_id + offset >= BIT_ULL(dev->num_eventid_bits)`.
- Checks the handler makes and restore does not: see "Restoring the tables".
