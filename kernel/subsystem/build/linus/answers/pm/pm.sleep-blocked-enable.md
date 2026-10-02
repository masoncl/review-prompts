- `pm_runtime_block_if_disabled()`: returns true for every device whose
  runtime PM is disabled; it sets `power.last_status` to `RPM_BLOCKED` only if
  that field is still `RPM_INVALID`.
- `__pm_runtime_disable()`: stores the real status in `power.last_status` when
  it disables an enabled device, so that device is not blocked; a device that
  was never enabled has `RPM_INVALID` there until it is blocked.
- `device_prepare_smart_suspend()`: a parent or supplier for which
  `pm_runtime_blocked()` is true does not prevent smart suspend of the child
  or consumer.
- `pm_runtime_enable()` on a blocked device: prints "Attempt to enable runtime
  PM when it is blocked", calls `dump_stack()`, then enables as usual and sets
  `power.last_status` to `RPM_INVALID`; nothing is refused.
- That warning is tested only when `power.disable_depth` reaches 0.
- `device_prepare()` when `->prepare()` returns a negative value: calls
  `pm_runtime_unblock()` and `pm_runtime_put()` itself; `dpm_prepare()` does
  not put the device on `dpm_prepared_list`.
