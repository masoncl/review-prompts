- `fflags`: `u64`; `dflags`: `unsigned long`, bits 0 to 8 defined in
  `drivers/usb/storage/usb.h`.
- `fflags` is written after probe with plain non-atomic `|=` and `&=`: see
  `sdev_configure()`, `usb_stor_invoke_transport()` and
  `usb_stor_Bulk_transport()`.
- `release_everything()`: drops the only `struct Scsi_Host` reference that
  usb-storage holds; nothing under `drivers/usb/storage/` calls
  `scsi_host_get()`.
- `dissociate_dev()`: takes or drops no `struct usb_device` reference; nothing
  under `drivers/usb/storage/` calls `usb_get_dev()` or `usb_get_intf()`.
- After `release_everything()` the freed pointers (`current_urb`, `extra`,
  `cr`, `iobuf`) keep their old values; only the interface data is set to
  NULL, so a NULL test on a field does not detect teardown.
- A `struct Scsi_Host` reference keeps the `struct us_data` memory; it does
  not keep `us->extra`, `us->iobuf`, `us->cr` or `us->current_urb`.
- **Potentially unsafe usage**: a timer, work item, private URB or input
  device set up by a sub-driver that reaches `us` or `us->extra`.
  - Unsafe: when it can still run or be queued after
    `us->extra_destructor()` returns; `usb_stor_release_resources()` then
    frees `us->extra` and `release_everything()` drops the host reference.
  - Safe: stopped synchronously inside the destructor, as
    `realtek_cr_destructor()` does with `timer_shutdown_sync()` under
    `CONFIG_REALTEK_AUTOPM` and `onetouch_release_input()` does with
    `usb_kill_urb()` and `input_unregister_device()`.
