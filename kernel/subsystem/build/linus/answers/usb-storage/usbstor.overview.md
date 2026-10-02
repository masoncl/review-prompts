- `struct us_unusual_dev`: carries no `US_FL_*` flags. The flags of an entry
  are in `driver_info` of the parallel `struct usb_device_id`;
  `get_device_info()` copies `id->driver_info` into `us->fflags`.
- State bits (`US_FLIDX_*`): held in `dflags`; `struct us_data` has no field
  named flags.
- `us->srb` hand-off: protected by the host lock (`scsi_lock()` in
  `drivers/usb/storage/usb.h`), not by `us->dev_mutex`.
- `us->max_lun` is the device's LUN limit; the thread rejects a higher LUN
  with `DID_BAD_TARGET`. usb-storage writes the host's `max_lun` only in
  `usb_stor_scan_dwork()`, when `us->max_lun >= 8`.
- `us->extra` is not always set between `usb_stor_probe1()` and
  `usb_stor_probe2()`. For example `init_alauda()` sets it as the
  `initFunction` run inside `usb_stor_probe2()`, and `datafab_transport()`
  sets it on the first command.
- Host template: `usb_stor_host_template` in
  `drivers/usb/storage/scsiglue.c` is a `static const` master. Each
  sub-driver module, and `usb-storage` itself, has its own non-const copy,
  filled by `usb_stor_host_template_init()` from `module_usb_stor_driver()`.
- `uas` intfdata: the `struct Scsi_Host`, not the `struct uas_dev_info`. In
  `usb-storage` the intfdata is the `struct us_data`.
- `struct uas_dev_info` is reached through `shost->hostdata`, and through
  `sdev->hostdata` once `uas_sdev_init()` has set it.
- `uas` and `usb-storage` share more than tables. `uas` uses
  `usb_stor_adjust_quirks()` and `usb_stor_sense_invalidCDB`, both exported
  by `usb-storage`.
- `uas_usb_ids` also matches the Bulk-Only interface (`USB_PR_BULK`), so both
  drivers match the same interface. `uas_use_uas_driver()` in
  `drivers/usb/storage/uas-detect.h` is compiled into both and decides:
  `storage_probe()` declines when it returns 1, `uas_probe()` when it
  returns 0.
