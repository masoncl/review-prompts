- Handlers installed in `uas_host_template`: `.eh_abort_handler =
  uas_eh_abort_handler` and `.eh_host_reset_handler =
  uas_eh_host_reset_handler`; there is no uas_eh_device_reset_handler() here.
- `.eh_device_reset_handler`, `.eh_target_reset_handler`,
  `.eh_bus_reset_handler`: not set by uas; `scsi_try_bus_device_reset()`,
  `scsi_try_target_reset()` and `scsi_try_bus_reset()` in
  `drivers/scsi/scsi_error.c` return `FAILED` for a NULL handler, so the only
  reset step of SCSI EH that reaches uas is the host reset.
- Per-device template hooks: `.sdev_init = uas_sdev_init` and
  `.sdev_configure = uas_sdev_configure`; the template has no slave_alloc
  member.
- `uas_eh_abort_handler()`: acts on the one command passed in; it kills only
  that command's in-flight data URBs with `usb_kill_urb()`, touches no
  anchor, and has no warning for an already set `COMMAND_ABORTED`; there is
  no uas_abort_work here.
- `uas_eh_host_reset_handler()`: after `usb_lock_device_for_reset()` it sets
  `devinfo->resetting`, kills the `cmd_urbs`, `sense_urbs` and `data_urbs`
  anchors, calls `uas_zap_pending()` with `DID_RESET`, calls
  `usb_reset_device()`, clears `resetting`, then `usb_unlock_device()`.
- `usb_reset_device()` in `drivers/usb/core/hub.c`: calls `uas_pre_reset()`
  before and `uas_post_reset()` after the port reset, so on the host reset
  path both run inside `uas_eh_host_reset_handler()` with `resetting` set and
  the table already zapped.
- `uas_pre_reset()`: does not set `resetting` and kills no URB; it blocks the
  host and waits in `uas_wait_for_pending_cmnds()`; it returns 0 or 1, never
  a negative errno.
- `uas_pre_reset()` returning 1: `usb_reset_device()` calls
  `usb_forced_unbind_intf()` before the port reset and does not call
  `uas_post_reset()` for that interface.
- `uas_post_reset()`: does not clear `resetting`, does not call
  `uas_zap_pending()` and submits no URB itself.
- `uas_post_reset()` returning 1: sets `needs_binding`;
  `usb_unbind_and_rebind_marked_interfaces()` is called only when the port
  reset returned 0.
- Completion while `devinfo->resetting`: `uas_stat_cmplt()` returns without
  clearing `COMMAND_INFLIGHT`; `uas_data_cmplt()` clears its in-flight bit
  and URB pointer first, then returns without `uas_try_complete()`.
- `uas_zap_pending()`: walks `devinfo->cmnd[]` only, so a command whose slot
  `uas_eh_abort_handler()` cleared is not completed by it.
- `uas_disconnect()`: kills the three anchors between
  `cancel_work_sync(&devinfo->work)` and `uas_zap_pending()` with
  `DID_NO_CONNECT`, and calls `cancel_work_sync(&devinfo->scan_work)` before
  `scsi_remove_host()`.
- `uas_shutdown()`: returns at once unless `system_state == SYSTEM_RESTART`;
  only then does it set `devinfo->shutdown`, free the streams and reset.
- **Unsafe usage**: calling `uas_zap_pending()` while a data URB of a
  command in `devinfo->cmnd[]` is still in flight.
  - Unsafe: `uas_try_complete()` returns `-EBUSY` on the data in-flight bit,
    the `WARN_ON()` in `uas_zap_pending()` fires and the command stays in
    its slot.
  - Safe: set `devinfo->resetting`, then kill the `data_urbs` anchor first,
    as `uas_disconnect()` does; `uas_data_cmplt()` clears the in-flight bit
    even while `resetting`.
- **Unsafe usage**: calling `usb_kill_urb()` or `usb_kill_anchored_urbs()`
  while holding `devinfo->lock`.
  - Unsafe: `usb_kill_urb()` has `might_sleep()` and waits for the
    completion handler, and `uas_data_cmplt()` takes `devinfo->lock`.
  - Safe: take `usb_get_urb()` references under the lock, drop the lock,
    then `usb_kill_urb()` and `usb_put_urb()`, as `uas_eh_abort_handler()`
    does.
