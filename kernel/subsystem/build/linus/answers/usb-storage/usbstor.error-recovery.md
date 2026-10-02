- Order at `Handle_Errors`: `usb_stor_port_reset()` first.
  `us->transport_reset()`, the class-specific reset, runs only if the port
  reset returned < 0.
- Before either reset: `US_FLIDX_RESETTING` is set and `US_FLIDX_ABORTING`
  cleared under the host lock. With `US_FLIDX_ABORTING` set,
  `usb_stor_msg_common()` returns `-EIO` and the class reset could send
  nothing.
- `us->dev_mutex`: released by `usb_stor_invoke_transport()` around
  `usb_stor_port_reset()` only, and retaken after.
  `usb_stor_port_reset()` itself never touches it.
- Reason: `usb_reset_device()` calls `usb_stor_pre_reset()`, which takes
  `us->dev_mutex`; `usb_stor_post_reset()` releases it.
- `us->transport_reset()`: runs with `us->dev_mutex` held.
- Reset outcome: the return value of `us->transport_reset()` is discarded,
  and neither reset changes `srb->result`.
- `usb_stor_port_reset()` returns an error without resetting when:
  - `us->pusb_dev->quirks & USB_QUIRK_RESET`: `-EPERM`, before any lock is
    tried;
  - `usb_lock_device_for_reset()` fails: device state
    `USB_STATE_NOTATTACHED` or `USB_STATE_SUSPENDED`, interface condition
    `USB_INTERFACE_UNBINDING` or `USB_INTERFACE_UNBOUND`, or the device lock
    not obtained within one second of polling (`-EBUSY`);
  - `US_FLIDX_DISCONNECTING` is set once the lock is held: `-EIO`.
- `usb_stor_port_reset()` makes no test for `USB_STATE_CONFIGURED`.
- A negative return from `usb_reset_device()` itself also leads to the class
  reset.
