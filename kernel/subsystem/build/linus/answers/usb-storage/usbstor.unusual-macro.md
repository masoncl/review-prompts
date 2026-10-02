- Subclass codes such as `USB_SC_SCSI` and protocol codes such as
  `USB_PR_BULK`: both families are defined in `include/linux/usb/storage.h`,
  and nowhere under `drivers/usb/storage/`.
- Override codes usable in `drivers/usb/storage/unusual_devs.h`:
  `USB_SC_DEVICE`, `USB_PR_DEVICE`, and otherwise only those with a case in
  `get_protocol()` and `get_transport()` in `drivers/usb/storage/usb.c`.
- Any other resulting code: no handler is set, and `usb_stor_probe2()` returns
  `-ENXIO`. For example `USB_SC_LOCKABLE` and `USB_PR_UAS` have no case.
- Driver-private codes, for example `USB_SC_ISD200` or `USB_PR_JUMPSHOT`:
  valid only in a sub-driver header, whose probe sets the handlers itself
  between `usb_stor_probe1()` and `usb_stor_probe2()`.
