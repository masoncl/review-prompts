- Devres release: `hid_device_remove()` in `drivers/hid/hid-core.c` calls
  `devres_release_group()` on `hdev->devres_group_id` right after the
  callback (or the default `hid_hw_stop()`), before `hid_close_report()` and
  before `hdev->driver = NULL`; it does not call `devres_release_all()`.
- Devres group: `__hid_device_probe()` opens it and never closes it, so a
  `devm_*` resource added to `&hdev->dev` after probe is released at the same
  point.
- `driver_input_lock` during the release: still held, unless the callback
  left io started.
- `hid_device_io_start()` inside `remove`: releases the semaphore early; the
  final `up()` is skipped only if `hdev->io_started` is still true at the
  end.
- `hdrv->raw_event`: called only from `__hid_input_report()`, so it cannot
  run while `hid_device_remove()` holds the semaphore.
- Listener callbacks: not gated by the semaphore; an input callback on a
  hidinput `struct input_dev`, such as `sony_play_effect()` in
  `drivers/hid/hid-sony.c`, can still enter the driver until `hid_hw_stop()`
  has run.
