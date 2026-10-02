- Reports during `remove`: cannot queue work or re-arm a timer, because the
  core holds `driver_input_lock` for the whole callback unless the driver
  calls `hid_device_io_start()`.
- Sources that stay live in `remove`: input callbacks until
  `hid_hw_stop()`, class devices until unregistered, and the work or timer
  itself.
- After `remove` or a failed probe returns: `devres_release_group()` frees
  `devm_kzalloc()` driver data at once, so every cancel has to be
  synchronous and finished by then.
- **Unsafe usage**: calling `hid_hw_stop()` while a timer or work that uses
  the hidinput `struct input_dev` can still run; `hidinput_disconnect()`
  unregisters and frees those devices.
  - Safe: kill the timer first, as `uclogic_remove()` in
    `drivers/hid/hid-uclogic-core.c` (`timer_shutdown_sync()`) and
    `mt_remove()` in `drivers/hid/hid-multitouch.c` (`timer_delete_sync()`)
    do; the held `driver_input_lock` keeps reports from re-arming it.
- **Potentially unsafe usage**: cancelling work in `remove` while a class
  device that queues it is still registered.
  - Unsafe: when the class device was registered with `devm_*` on
    `&hdev->dev` and its callback queues unconditionally; it is unregistered
    only after `remove` returns and can queue the work after the cancel.
  - Safe: the callback tests a flag under the lock that `remove` clears
    before `cancel_work_sync()`, as `dualsense_schedule_work()` with
    `dualsense_remove()` in `drivers/hid/hid-playstation.c`, and
    `sony_schedule_work()` with `sony_cancel_work_sync()` in
    `drivers/hid/hid-sony.c`.
  - Safe: the class device is unregistered explicitly first, as
    `gt683r_led_remove()` in `drivers/hid/hid-gt683r.c` calls
    `led_classdev_unregister()` before `flush_work()` and `hid_hw_stop()`.
- **Potentially unsafe usage**: on the probe error path, cancelling
  report-armed work before `hid_hw_stop()`.
  - Unsafe: after `hid_device_io_start()`, when `raw_event` can queue the
    work again between the cancel and the stop.
  - Safe: stop first, then cancel, as the `hid_hw_open_fail` and
    `hid_hw_start_fail` labels of `hidpp_probe()` in
    `drivers/hid/hid-logitech-hidpp.c`; `hid_hw_stop()` re-takes
    `driver_input_lock` when `io_started` is set.
  - Safe: when probe never called `hid_device_io_start()`, as
    `sony_probe()` in `drivers/hid/hid-sony.c`; the core holds the lock for
    the whole probe.
