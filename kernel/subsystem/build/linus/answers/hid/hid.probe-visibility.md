- `input_mapping`, `input_mapped`, `input_configured`, `feature_mapping`: run
  only inside `hidinput_connect()`, so only when the mask has
  `HID_CONNECT_HIDINPUT`; never on incoming reports.
- `on_hid_hw_open` and `on_hid_hw_close`: called by `hid_hw_open()` and
  `hid_hw_close()` on the first open and last close, for example when user
  space opens the evdev or hidraw node. `driver_input_lock` does not hold
  them off.
- `suspend`, `resume`, `reset_resume`, under `CONFIG_PM`: reached through
  `hid_driver_suspend()`, `hid_driver_resume()` and
  `hid_driver_reset_resume()`, which take no lock and test only
  `hdev->driver`, set before `probe` is called. Transports call them from
  their own PM callbacks, for example `hid_suspend()` in
  `drivers/hid/usbhid/hid-core.c`.
- Hold-off of `raw_event`, `event` and `report`: sits only in
  `__hid_input_report()`. `hid_report_raw_event()` takes no lock; a caller
  that uses it directly, such as `drivers/staging/greybus/hid.c`, reaches
  `event` and `report` during probe.
- **Potentially unsafe usage**: setting or initialising driver private data
  after `hid_hw_start()`.
  - Unsafe: when the mask has `HID_CONNECT_HIDINPUT` and a mapping callback
    reads `hid_get_drvdata()`, or when `on_hid_hw_open` or an attribute or
    device already registered reads it.
  - Safe: when only `raw_event`, `event` or `report` read it and it is set
    before `hid_device_io_start()`, as in `cp2112_probe()` with mask
    `HID_CONNECT_HIDRAW`; `__hid_input_report()` drops reports until then.
  - Safe: when only `raw_event` reads it and probe never calls
    `hid_device_io_start()`, as `ps_probe()`, which sets drvdata in
    `dualshock4_create()`, after `hid_hw_open()`; `__hid_input_report()`
    drops reports until probe returns, and `ps_raw_event()` also tests for
    NULL.
  - Safe: set before `hid_hw_start()`, as `logi_dj_probe()` does, or before
    `hid_parse()` when `report_fixup` reads it, as `hidpp_probe()` does.
