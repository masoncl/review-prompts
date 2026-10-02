- `US_FLIDX_DISCONNECTING`: a bit in `us->dflags`; there is no
  US_FLAG_DISCONNECTING here.
- `quiesce_and_remove_host()` sets the bit under `scsi_lock()`, after
  `scsi_remove_host()` returns.
  - It sets it earlier only when `us->pusb_dev->state` is
    `USB_STATE_NOTATTACHED`.
  - On an unbind with the device present, commands can still run through the
    control thread and the sub-driver during `scsi_remove_host()`.
- `quiesce_and_remove_host()`: does not take `us->dev_mutex` itself, does not
  call `usb_stor_stop_transport()`, and completes no command.
- `scsi_remove_host()`: called unconditionally by
  `quiesce_and_remove_host()`.
- `wake_up(&us->delay_wait)`: wakes only a waiter in
  `usb_stor_reset_common()`; it does not complete `us->cmnd_ready`.
- `usb_stor_release_resources()` order: `complete(&us->cmnd_ready)`,
  `kthread_stop()`, `us->extra_destructor`, `kfree(us->extra)`,
  `usb_free_urb(us->current_urb)`.
- Sub-driver destructor: runs after `kthread_stop()` has returned, and before
  `dissociate_dev()` and `scsi_host_put()`.
- `dissociate_dev()`: frees `us->cr` and `us->iobuf` and clears the interface
  data; it does not free the URB.
- Exit signal: `usb_stor_release_resources()` does not write `us->srb`; the
  thread leaves its command loop because it finds `us->srb` NULL after the
  completion.
- Waiting for the control thread to exit: `kthread_stop()`;
  `struct us_data` has no completion for thread exit.
- Probe-failure path: `release_everything()` runs with
  `US_FLIDX_DISCONNECTING` clear; `us->srb` is NULL because the host was never
  added successfully.
