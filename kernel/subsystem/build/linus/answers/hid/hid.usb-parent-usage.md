- Non-usbhid creators that can produce a `BUS_USB` device, among the callers
  of `hid_allocate_device()`:

| Creator | `bus` comes from | `dev.parent` is |
|---|---|---|
| `uhid_dev_create2()` in `drivers/hid/uhid.c` | userspace | `uhid_misc.this_device` |
| `drivers/hid/hid-logitech-dj.c` | hard-coded `BUS_USB` | the receiver's `struct hid_device` |
| `steam_create_client_hid()` in `drivers/hid/hid-steam.c` | copied from the real device | copied from the real device |

- hid-steam client device: its parent can be a real USB interface, yet
  `hid_is_usb()` is false because `ll_driver` is `steam_client_ll_driver`.
- HID-BPF: creates no devices.
- Multi-transport guard: see `asus_probe()` in `drivers/hid/hid-asus.c`,
  which tests `hid_is_usb()` beside each `to_usb_interface()`.
