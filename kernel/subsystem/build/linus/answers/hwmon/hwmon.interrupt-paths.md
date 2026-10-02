- `lm90_irq_thread()`: does not call `hwmon_notify_event()`. Under the lock,
  `lm90_update_alarms_locked()` sends no event; it schedules `report_work`, and
  `lm90_report_alarms()` sends the events from the work item, without the core
  lock (see "Nesting the core lock").
- `lm90_stop_work()`: the devm action that cancels `alert_work` and
  `report_work`. `lm90_restore_conf()` only writes back the conversion rate
  and config registers.
- `lm90_probe()` order: registration, store `data->hwmon_dev`, add
  `lm90_stop_work()`, request the IRQ. Teardown therefore frees the IRQ,
  stops the work, and only then unregisters the hwmon device.
- **Potentially unsafe usage**: cancelling at teardown a work item that the
  callbacks can schedule.
  - Unsafe: when the hwmon device is still registered at that point and
    nothing stops a callback from scheduling the work again; the work then
    runs after the driver data is freed.
  - Safe: set a flag under the core lock before cancelling and test it where
    the work is scheduled. `lm90_stop_work()` sets `data->shutdown`;
    `lm90_update_alarms_locked()` returns 0 when it is set, and `lm90_alert()`
    tests it before `schedule_delayed_work()`.
