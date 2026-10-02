- When the action runs: inside `devres_release_group()`, so before
  `hid_close_report()` and before `hdev->driver = NULL`, both in
  `hid_device_remove()` and in a failed `__hid_device_probe()`.
- Lock state when the action runs: `__hid_device_probe()` calls
  `hid_device_io_stop()` first if probe left io started, so the action runs
  with `driver_input_lock` held; a probe error path after registration just
  returns the error.
- In-tree examples: `mcp2221_hid_unregister()` in
  `drivers/hid/hid-mcp2221.c` and `hammer_stop()` in
  `drivers/hid/hid-google-hammer.c`.
- `mcp2221_remove()`: empty except under `IS_REACHABLE(CONFIG_IIO)`, where
  it cancels `init_work`, which itself adds `devm_*` resources, before the
  group is released.
- `hammer_probe()`: when `hammer_has_folded_event()`, calls `hid_hw_open()`
  after registering the action, and `hammer_remove()` calls the matching
  `hid_hw_close()`, so the close still precedes the stop.
- **Unsafe usage**: a devres action that calls `hid_hw_stop()` in a driver
  with no `remove` callback, or whose `remove` also stops.
  - Safe: the driver sets a `remove` callback that does not call
    `hid_hw_stop()`, as `hammer_remove()` does; `hid_device_remove()` then
    skips its default stop and the action is the only stop.
