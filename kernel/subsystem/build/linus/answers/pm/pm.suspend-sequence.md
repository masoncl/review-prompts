- Task freezing: happens only with `CONFIG_SUSPEND_FREEZER`; without it
  `suspend_freeze_processes()` in `kernel/power/power.h` returns 0 and no
  task is frozen when the device callbacks run.
- Filesystem freeze: `suspend_prepare()` calls `filesystems_freeze()`
  unconditionally, before freezing tasks; `filesystem_freeze_enabled` is
  only its argument.
- `filesystem_freeze_enabled` false (the default): superblocks whose type
  sets `FS_POWER_FREEZE` are still frozen; `fs/efivarfs/super.c` sets it.
- `filesystem_freeze_enabled` true: every superblock with a `freeze_fs` or
  `freeze_super` operation is frozen; see `filesystems_freeze_callback()`
  in `fs/super.c`.
- Filesystem sync: `enter_state()` calls `pm_sleep_fs_sync()` in
  `kernel/power/main.c` only when `sync_on_suspend_enabled` is set; there
  is no sync_filesystems() function.
- `pm_sleep_fs_sync()`: runs `ksys_sync_helper()` from a work item and
  returns `-EBUSY` once `pm_wakeup_pending()` is true, which aborts the
  suspend before `suspend_prepare()`.
- Aborted sync: the work item is not cancelled, so `ksys_sync()` keeps
  running after `enter_state()` has returned.
- Signals: do not interrupt the sync; the wait is `wait_event_timeout()`.
- Console: there is no suspend_console(); `console_suspend_all()` in
  `kernel/printk/printk.c` marks consoles `CON_SUSPENDED` only when
  `console_suspend_enabled` is set.
- Driver probing: blocked from `dpm_prepare()` (`device_block_probing()`)
  until `dpm_complete()`.
- GFP mask: `pm_restrict_gfp_mask()` runs in `dpm_suspend_start()` after
  `dpm_prepare()`, so `->prepare` runs with `__GFP_IO` and `__GFP_FS`
  still allowed and `->suspend` without them.
- Late phase: `device_suspend_late()` calls `pm_runtime_disable()` for one
  device just before that device's callback; devices not yet processed,
  such as its parent, still have runtime PM enabled.
- Noirq phase: `suspend_device_irqs()` leaves enabled, besides armed wakeup
  interrupts, lines with an `IRQF_NO_SUSPEND` action, chained descriptors
  and nested-thread interrupts; see `suspend_device_irq()` in
  `kernel/irq/pm.c`.
- After noirq: `suspend_enter()` calls `pm_sleep_disable_secondary_cpus()`,
  not `suspend_disable_secondary_cpus()` directly; the wrapper calls
  `cpuidle_pause()` first.
