- `pmbus_lock()`: exists, exported, non-interruptible `mutex_lock()` on
  `update_lock`.
- `DEFINE_GUARD(pmbus_lock, ...)` in `drivers/hwmon/pmbus/pmbus.h`:
  `guard(pmbus_lock)(client)` and `scoped_guard(pmbus_lock, client)` are the
  forms the core uses at every lock site.
- `pmbus_lock_interruptible()`: has no guard class; pair it with
  `pmbus_unlock()` by hand.
- Exported accessors take no lock: for example `pmbus_set_page()`,
  `pmbus_read_word_data()`, `pmbus_write_byte()`, `pmbus_update_byte_data()`,
  `pmbus_update_fan()`, `pmbus_clear_faults()`,
  `pmbus_check_word_register()`.
- Exported entry points that take the lock themselves:
  `pmbus_check_and_notify_faults()` and the functions in
  `pmbus_regulator_ops`.
- Probe-time calls run without the lock: `pmbus_do_probe()` holds nothing
  around `pmbus_init_common()` (which calls `identify`) and
  `pmbus_find_attributes()`. A callback therefore runs unlocked from those
  two functions and locked at run time.
- Nothing asserts the lock: `drivers/hwmon/pmbus/` has no
  `lockdep_assert_held()`. A missing lock fails silently as a wrong-page
  access.
- hwmon core lock: `hwmon_attr_show()`, `hwmon_attr_show_string()` and
  `hwmon_attr_store()` in `drivers/hwmon/hwmon.c` hold the hwmon device's
  mutex around `struct hwmon_ops` callbacks. PMBus attributes are plain group
  attributes and never pass through them.
- `hwmon_lock()`: locks that same hwmon-device mutex, a different mutex from
  `update_lock`. Nothing in `drivers/hwmon/pmbus/` calls it, and holding it
  does not exclude the PMBus core.
- `drivers/hwmon/pmbus/ucd9000.c`: contains no call to the lock helpers; it is
  not an example of the locking pattern.
- **Unsafe usage**: taking `update_lock` from code the core runs with the
  lock held.
  - Unsafe: `pmbus_lock()`, `pmbus_lock_interruptible()`,
    `pmbus_check_and_notify_faults()` or a `pmbus_regulator_ops` function
    called from a `struct pmbus_driver_info` read/write callback. The mutex
    is not recursive and `pmbus_show_sensor()` already holds it; the task
    deadlocks.
  - Safe: a callback calls the unlocked accessors, as
    `ibm_cffps_read_word_data()` does.
  - Safe: `pmbus_check_and_notify_faults()` from a context that holds no
    PMBus lock, as `mpq8646_alarm_poll_work()` does.
- **Potentially unsafe usage**: reaching the chip from a chip driver's own
  entry point (sysfs group, debugfs, GPIO, LED, nvmem, work item) without
  `update_lock`, once `pmbus_do_probe()` has returned.
  - Unsafe: on a chip with more than one page or with phases:
    `pmbus_set_page()` skips the PAGE write when `currpage` matches, and
    reads and writes `currpage`/`currphase` unlocked. A concurrent core
    access lands on the wrong page.
  - Safe: bracket the whole sequence with the lock, as
    `isl68137_avs_enable_store_page()` (interruptible, result checked) and
    `adm1266_gpio_get()` (guard) do.
  - Safe: one `i2c_smbus_read_byte_data()`-style transfer on a chip whose
    info has `pages` 1 and no `phases`, as `ipsps_mode_show()` in
    `drivers/hwmon/pmbus/inspur-ipsps.c`; `pmbus_set_page()` writes PAGE
    only when `info->pages > 1`.
- **Unsafe usage**: calling `pmbus_lock()`, `pmbus_lock_interruptible()` or
  `pmbus_unlock()` before `pmbus_do_probe()`.
  - Unsafe: the helpers dereference `i2c_get_clientdata()`, which is NULL
    until `pmbus_do_probe()` sets it.
  - Safe: lock only after `pmbus_do_probe()` succeeded, as
    `adm1266_probe()` does when it calls `adm1266_rtc_set()`.
