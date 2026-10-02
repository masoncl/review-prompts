- Sleeping points: `kernfs_find_and_get_ns()` under `sysfs_notify()` does
  `down_read()`; `kobject_uevent_env()` allocates with `GFP_KERNEL`;
  `thermal_zone_device_update()` takes the zone mutex.
- **Unsafe usage**: calling `hwmon_notify_event()` from a hard interrupt
  handler or any other atomic context; it sleeps at the points above.
  - Safe: from a threaded handler requested with a NULL primary handler, as
    `adt7x10_irq_handler()` is in `adt7x10_probe()`.
  - Safe: from a work item, as `lm90_report_alarms()`.
- **Unsafe usage**: a notifier that can still run while the hwmon device is
  unregistered; `hwmon_thermal_notify()` walks `hwdev->tzdata` with no lock
  and `hwmon_thermal_remove_sensor()` does `list_del()` on it.
  - Safe: stop the work and the interrupt first; in `lm90_probe()` the
    `lm90_stop_work()` devm action and the devm IRQ are added after the devm
    registration, so both are released before `devm_hwmon_release()`
    unregisters the hwmon device.
