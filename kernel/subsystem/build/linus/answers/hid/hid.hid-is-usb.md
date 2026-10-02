- `hid_is_usb()`: an out-of-line function in `drivers/hid/usbhid/hid-core.c`
  with `EXPORT_SYMBOL_GPL`, so it lives in the usbhid module.
- `include/linux/hid.h`: has only the `extern` declaration, under no `#if`;
  there is no inline version and no stub for `CONFIG_USB_HID=n`.
- `usb_hid_driver`: `static const` in that file and not exported; there is no
  hid_is_using_ll_driver() in this tree.
- Inherited dependency: enough when a parent symbol depends on `USB_HID`, as
  `HID_LOGITECH_HIDPP` does through `HID_LOGITECH`.
- Callers outside `drivers/hid`: need the same dependency, as
  `SENSORS_ARCTIC_FAN_CONTROLLER` in `drivers/hwmon/Kconfig` has.
