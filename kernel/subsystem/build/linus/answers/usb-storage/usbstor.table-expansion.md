- Index into `us_unusual_dev_list[]`: the pointer difference
  `id - usb_storage_usb_ids`, computed in `storage_probe()`.
- `usb_storage_usb_ids[]`: built in `drivers/usb/storage/usual-tables.c`;
  only `us_unusual_dev_list[]` is built in `drivers/usb/storage/usb.c`. Both
  are expansions of `drivers/usb/storage/unusual_devs.h`, each under its own
  definitions of the entry macros.
- Generic `USUAL_DEV()` lines: the last lines of `unusual_devs.h`, so they
  come before the `{ }` terminator in both arrays, not after it.
- Entry macros in `unusual_devs.h`: the header may use only `UNUSUAL_DEV()`,
  `COMPLIANT_DEV()` and `USUAL_DEV()`.
- Run-time id: recognised because the `id` pointer lies outside
  `usb_storage_usb_ids[]`, not by its `driver_info`; `usb_probe_interface()`
  in `drivers/usb/core/driver.c` passes a copy on its own stack.
- `for_dynamic_ids`: `USUAL_DEV(USB_SC_SCSI, USB_PR_BULK)`, so names and
  `initFunction` are `NULL` and both overrides are explicit.
- Flags of a run-time id: `usb_store_new_id()` leaves `driver_info` 0, or
  copies it from a static entry when a reference VID and PID are written to
  `new_id`.
- Run-time id with a reference entry: gets that entry's flags, but not its
  overrides, names or init function.
