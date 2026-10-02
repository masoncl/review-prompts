- **Unsafe usage**: calling `hwmon_notify_event()` with type `hwmon_temp`
  while the core lock is held (inside a callback or under `hwmon_lock()`).
  With an enabled thermal zone attached to that channel,
  `hwmon_thermal_notify()` calls `thermal_zone_device_update()`, which
  reaches `hwmon_thermal_get_temp()` and takes the same lock again.
  - Safe: schedule a work item under the lock and send the event from the
    work item without the lock, as `lm90_report_alarms()` does for
    `report_work`.
  - Safe: call it from a handler that holds no lock, as
    `lm75_alarm_handler()` does.
- **Unsafe usage**: `cancel_work_sync()` or `cancel_delayed_work_sync()`
  under the core lock, on a work item that itself takes the core lock.
  - Safe: drop the lock first; `lm90_stop_work()` leaves its
    `scoped_guard(hwmon_lock, ...)` before it cancels `alert_work`.
  - Safe: under the lock use `cancel_delayed_work()`, as
    `lm90_update_alarms_locked()` does.
