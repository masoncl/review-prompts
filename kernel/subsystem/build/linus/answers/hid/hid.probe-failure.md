- Order in `__hid_device_probe()` on error: `hid_device_io_stop()` when
  `hdev->io_started` is set, `devres_release_group()`, `hid_close_report()`,
  `hdev->driver = NULL`.
- **Potentially unsafe usage**: returning an error from `probe` after
  `hid_hw_start()` succeeded, without `hid_hw_stop()`.
  - Unsafe: when nothing else stops the hardware. `__hid_device_probe()`
    calls neither `hid_hw_stop()` nor `hid_hw_close()`; the nodes made by
    `hid_connect()` stay registered while `hid_close_report()` frees the
    reports.
  - Safe: when a devm action on `&hdev->dev` closes and stops, as
    `mcp2221_hid_unregister()` registered in `mcp2221_probe()`; the
    `devres_release_group()` of the core runs it.
