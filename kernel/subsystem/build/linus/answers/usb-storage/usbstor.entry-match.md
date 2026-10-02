- Revision compare: plain unsigned 16-bit in `usb_match_device()`, not BCD
  digit by digit.
- Upper bound `0x9999`: excludes a device whose `bcdDevice` is above it; the
  table uses both `0x9999` and `0xffff` as "all revisions".
- UNUSUAL_VENDOR_INTF: not in this tree; no entry macro here combines a
  vendor or product id with interface fields, so an entry cannot be limited
  to one interface of a composite device.
- Interface class: neither `storage_probe()` nor `usb_stor_probe1()` rejects
  an interface for its `bInterfaceClass`.
- Non-storage interface, entry with `USB_SC_DEVICE` or `USB_PR_DEVICE`:
  `usb_stor_probe2()` returns `-ENXIO` unless the descriptor's code has a case
  in `get_protocol()` or `get_transport()`.
- Non-storage interface, entry with both overrides explicit: no class test
  stops it; `get_pipes()` needs only a bulk-in and a bulk-out endpoint, plus
  an interrupt-in endpoint for `USB_PR_CBI`.
- Run-time id with the VID and PID of a table entry: matched first by
  `usb_probe_interface()`, so the table entry's overrides, names and init
  function are not used.
- `storage_probe()`: passes its own matched id to `uas_use_uas_driver()`, so
  it does not see `US_FL_IGNORE_UAS` set only in a later `unusual_uas.h` entry.
