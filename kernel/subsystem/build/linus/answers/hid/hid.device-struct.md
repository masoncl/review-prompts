- `hdev->driver_data`: belongs to the code that called
  `hid_allocate_device()` for this device and is set before
  `hid_add_device()`; the bound driver's pointer is the `hdev->dev` drvdata.
- `i2c_hid_core_probe()`: stores the `struct i2c_client *` in `driver_data`,
  not its own state struct.
- Child devices: a HID driver that allocates them is their transport, so
  `drivers/hid/hid-logitech-dj.c` and `drivers/hid/hid-steam.c` write
  `driver_data` on the devices they created, never on the one they bind to.
- **Potentially unsafe usage**: a bound driver casting `hdev->driver_data` to
  `struct usbhid_device *`.
  - Unsafe: when the only evidence is `hdev->bus == BUS_USB` or the id table;
    devices from `drivers/hid/uhid.c` and `drivers/hid/hid-logitech-dj.c`
    can carry `BUS_USB` with another type there.
  - Safe: after `hid_is_usb()` returned true, as `u2fzero_probe()` checks
    before `u2fzero_fill_in_urb()` reads it; `usbhid_probe()` is what stores
    that type and sets the `ll_driver` that `hid_is_usb()` compares.
- Driver quirk bits read during start or connect: the deadline is
  `hid_hw_start()`; `drivers/hid/hid-core.c` reads `hdev->quirks` in
  `hid_connect()`, `hid_check_device_match()` and `hid_set_group()`, not in
  `hid_open_report()`.
- `hdev->claimed`: transports write it too, zeroing it in their `->stop()`
  (for example `usbhid_stop()`); no bound driver writes it.
