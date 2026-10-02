- `get_transport()` and `get_protocol()`: run at the end of
  `usb_stor_probe1()`, so `usb_stor_probe2()` does not overwrite the handlers
  the caller sets in between.
- `us->transport` and `us->proto_handler`: must be non-NULL on entry to
  `usb_stor_probe2()`, else `-ENXIO`.
- `initFunction`: runs inside `usb_stor_probe2()`, from
  `usb_stor_acquire_resources()`, not between the halves.
  - It runs after `get_pipes()` and the `us->current_urb` allocation, and
    before `kthread_run()`.
  - It may replace the handlers after the NULL check, as
    `usbat_set_transport()` does, and `realtek_cr_autosuspend_setup()` under
    `CONFIG_REALTEK_AUTOPM`.
- Between the halves `us->current_urb` is NULL and the pipe fields are unset,
  so the transfer helpers in `drivers/usb/storage/transport.c` cannot be used
  there.
- `us->max_lun` set between the halves is overwritten:
  - by `usb_stor_probe2()` when `US_FL_SCM_MULT_TARG` or `US_FL_SINGLE_LUN` is
    set;
  - by `usb_stor_scan_dwork()` when `us->protocol` is `USB_PR_BULK` and
    neither flag is set.
- `usb_stor_probe2()` order: control thread, then
  `usb_autopm_get_interface_no_resume()`, then `scsi_add_host()`.
- `scsi_scan_host()`: not called by `usb_stor_probe2()`; it runs later from
  `usb_stor_scan_dwork()`, which probe2 only queues.
- `usb_stor_probe1()` failure: calls `release_everything()` on every failure
  after `scsi_host_alloc()` succeeded.
- `*pus`: written right after `scsi_host_alloc()` succeeds, so after any later
  failure of `usb_stor_probe1()` it is non-NULL and dangling; when
  `scsi_host_alloc()` itself fails it is not written.
- **Unsafe usage**: returning an error between the halves without calling
  `usb_stor_probe2()`.
  - Unsafe: `release_everything()` is static in `drivers/usb/storage/usb.c`
    and nothing exported undoes `usb_stor_probe1()` alone, so the host,
    `us->cr`, `us->iobuf` and any `us->extra` leak.
  - Safe: do the fallible setup in `initFunction`, where a failure reaches
    `release_everything()` through probe2, as `rio_karma_init()` does.
- **Potentially unsafe usage**: calling `usb_stor_disconnect()` from a probe
  routine.
  - Unsafe: after either half returned non-zero; the interface data is NULL,
    so `usb_stor_disconnect()` dereferences NULL.
  - Safe: after `usb_stor_probe2()` returned 0 and a later step failed, as
    `ene_ub6250_probe()` does; nothing has been released yet.
