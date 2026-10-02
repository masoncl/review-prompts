- `power.smart_suspend`: stored as false by `device_prepare()` for every
  device whose runtime PM is disabled when it runs;
  `pm_runtime_block_if_disabled()` returns true and
  `device_prepare_smart_suspend()` is not called. `device_prepare()` stores
  nothing when it returns early for `power.syscore` or for a negative
  `->prepare()` value.
- `pm_runtime_force_resume()` clears `power.smart_suspend`, so
  `dev_pm_skip_suspend()` returns false for that device afterwards.
- Core tests: `device_suspend_late()`, `device_suspend_noirq()`,
  `device_resume_noirq()` and `device_resume_early()` skip the driver
  callback on the helpers only when the device has no `pm_domain`, `type`,
  `class` or `bus` callback for that phase; a middle layer with a callback
  must test them itself.
- `dev_pm_skip_resume()` on `PM_EVENT_THAW`: returns
  `dev_pm_skip_suspend(dev)`, not `power.must_resume`.
- `dev_pm_skip_resume()` on any event other than `PM_EVENT_RESTORE` and
  `PM_EVENT_THAW`: returns `!power.must_resume`; that includes
  `PM_EVENT_RECOVER`.
- `power.must_resume` in `device_suspend_noirq()`: set when
  `DPM_FLAG_MAY_SKIP_RESUME` is clear, or `power.may_skip_resume` is clear,
  or `pm_runtime_need_not_resume()` is false.
- `pm_runtime_need_not_resume()`: false when the usage count is above 1, or
  when `power.child_count` is nonzero and `power.ignore_children` is clear.
- Wakeup: the core has no wakeup test for `power.must_resume`;
  `pci_pm_suspend_noirq()` and `acpi_subsys_suspend_noirq()` clear
  `power.may_skip_resume` for a device that can wake up but is not enabled
  to, as their last step, so not after an earlier return such as the one on
  `dev_pm_skip_suspend()`.
- `dpm_superior_set_must_resume()`: sets `power.must_resume` in the parent
  and in every supplier, with no test of link flags or status;
  `device_prepare_smart_suspend()` looks at `DL_FLAG_PM_RUNTIME` links only.
- `device_resume_noirq()` when the resume is skipped: calls
  `pm_runtime_set_suspended()`.
- `device_resume_noirq()` when the resume is not skipped: calls
  `pm_runtime_set_active()` if `dev_pm_smart_suspend()` is true; there is no
  set_active field in `struct dev_pm_info`.
- Both status calls: made before the callback lookup, so also when a
  middle-layer callback runs; their return values are ignored.
- No status change: for a device that leaves `device_resume_noirq()` early
  (`power.syscore`, `power.direct_complete`, `power.is_noirq_suspended`
  clear, or `dpm_wait_for_superior()` false).
- Aborted noirq suspend: for a device with `power.is_noirq_suspended` clear
  and `dev_pm_skip_suspend()` true, `device_resume_noirq()` clears
  `power.must_resume`, so `dev_pm_skip_resume()` is true in the early phase
  unless the event is `PM_EVENT_RESTORE`.
