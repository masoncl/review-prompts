- `usb_stor_stop_transport()`: has one caller, `command_abort_matching()`,
  reached from `command_abort()` and `device_reset()`; it is skipped when
  `US_FLIDX_RESETTING` is set.
- `usb_stor_msg_common()` and `usb_stor_bulk_transfer_sglist()`: test only
  `US_FLIDX_ABORTING`, never `US_FLIDX_DISCONNECTING`.
- The comment block above `usb_stor_blocking_completion()` in
  `drivers/usb/storage/transport.c` describes a disconnect cancel and a
  `US_FLIDX_DISCONNECTING` test in the submit path; the code has neither.
- `US_FLIDX_DISCONNECTING` is tested in `queuecommand_lck()`,
  `usb_stor_reset_common()` and `usb_stor_port_reset()` only.
- `usb_stor_bulk_transfer_sglist()` with `US_FLIDX_ABORTING` set: returns
  `USB_STOR_XFER_ERROR` with `*act_len = 0`, not an errno, and has no timeout
  (`usb_sg_wait()`).
- `usb_stor_msg_common()` and `usb_stor_bulk_transfer_sglist()` are static;
  sub-drivers reach them through the exported helpers in
  `drivers/usb/storage/transport.c`, for example
  `usb_stor_bulk_transfer_buf()`, `usb_stor_bulk_srb()` and
  `usb_stor_control_msg()`.
- Sub-driver code that runs its own protocol through those helpers: for
  example `rts51x_bulk_transport()` in `drivers/usb/storage/realtek_cr.c` and
  `ene_send_scsi_cmd()` in `drivers/usb/storage/ene_ub6250.c`.
- `drivers/usb/storage/uas.c`: does not use `struct us_data` or these helpers.
- **Potentially unsafe usage**: `usb_bulk_msg()`, `usb_control_msg()` or a
  private URB in a usb-storage sub-driver.
  - Unsafe: on a path reached from `us->transport()` or `us->proto_handler()`;
    `usb_stor_stop_transport()` cancels only `us->current_urb` and
    `us->current_sg`, so `command_abort_matching()` stays in
    `wait_for_completion(&us->notify)` until that I/O ends or times out by
    itself.
  - Safe: in an `initFunction`, which `usb_stor_acquire_resources()` calls
    before `kthread_run()`, as `sierra_ms_init()` does with
    `usb_control_msg()`.
  - Safe: a URB that serves no SCSI command and is killed in the
    `extra_destructor`, as the interrupt URB in
    `drivers/usb/storage/onetouch.c`.
- **Potentially unsafe usage**: calling the helpers outside the control thread.
  - Unsafe: without `us->dev_mutex` once `usb_stor_probe2()` has started the
    control thread; the helpers use `us->current_urb`, `us->current_sg` or
    `us->cr`, which a command that may be running uses too.
  - Safe: with `us->dev_mutex` held, which `usb_stor_control_thread()` holds
    while it runs a command, as `usb_stor_scan_dwork()` and `device_reset()`
    do.
  - Safe: in an `initFunction`, which `usb_stor_acquire_resources()` calls
    before `kthread_run()` and before `scsi_add_host()`, as
    `usb_stor_euscsi_init()` does.
