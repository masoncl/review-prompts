- Models take `pm_runtime_reinit()` to zero `power.runtime_error`. It
  returns at once while runtime PM is enabled, and clears the field only
  through `pm_runtime_set_suspended()`, when the device is disabled and its
  status is `RPM_ACTIVE`. Besides `pm_runtime_init()`, only
  `__pm_runtime_set_status()` clears it.
- Models take `device_suspend_late()` to call
  `__pm_runtime_disable(dev, false)`, so that a pending resume request is
  dropped. `pm_runtime_remove()` is the only caller that passes false.
- Models take filesystems to be frozen for sleep only when
  `/sys/power/freeze_filesystems` is set. `hibernate()` calls
  `filesystems_freeze()` whatever `filesystem_freeze_enabled` is, as
  `suspend_prepare()` does; see "System state during device callbacks" for
  what is then frozen.
- Models take `RUNTIME_PM_OPS()` to wrap its members in `pm_ptr()`. In
  `include/linux/pm.h` only `SYSTEM_SLEEP_PM_OPS()`,
  `LATE_SYSTEM_SLEEP_PM_OPS()` and `NOIRQ_SYSTEM_SLEEP_PM_OPS()` wrap their
  members, with `pm_sleep_ptr()`.
- Models take `pm_wakeup_clear()` to take no argument and to run in
  `suspend_prepare()`. It takes an IRQ number and resets `pm_abort_suspend`
  only for 0; `freeze_processes()` and `pm_sleep_fs_sync()` call it with 0.
- Models place `pm_restrict_gfp_mask()` in the suspend core. For its caller
  on the suspend path see "System-wide locks"; `pm_restrict_gfp_mask()` and
  `pm_restore_gfp_mask()` nest through `saved_gfp_count` in
  `kernel/power/main.c`.
