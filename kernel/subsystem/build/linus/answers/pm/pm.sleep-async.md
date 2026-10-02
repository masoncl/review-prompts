- `dpm_wait()`: waits when the caller is async, or when `pm_async_enabled`
  is set and the target has `power.async_suspend`; it returns at once for a
  target with `power.no_pm`.
- `dpm_wait()` does not test `pm_trace_is_enabled()`; `is_async()` does.
- Links skipped by `dpm_wait_for_suppliers()` and `dpm_wait_for_consumers()`:
  `DL_STATE_DORMANT` links and links for which
  `device_link_flag_is_sync_state_only()` is true.
- `is_async()`: has no test for PM callbacks; a device without callbacks is
  async if the three conditions hold.
- `__dpm_async()`: calls `async_schedule_dev_nocall()`, not
  `async_schedule_dev()`; when it returns false the reference is dropped,
  and when that happens under `dpm_async_fn()` the list walk handles the
  device synchronously.
- Start of async work, in each of the six phases:
  1. the first walk starts async work only for `dpm_leaf_device()` devices
     (suspend) or `dpm_root_device()` devices (resume);
  2. a finished device starts its parent and suppliers through
     `dpm_async_suspend_superior()`, or its children and consumers through
     `dpm_async_resume_subordinate()`;
  3. the main walk calls `dpm_async_fn()` for every device; it does nothing
     more when `power.work_in_progress` is already set.
- `dpm_async_suspend_superior()`: not called when the device failed or
  `async_error` is set.
- `async_wip_mtx`: guards `power.work_in_progress`; see `dpm_async_fn()` and
  `dpm_async_with_cleanup()`. `dpm_clear_async_state()` resets the field
  under `dpm_list_mtx` instead.
- Phase barrier: each of the six phases ends with `async_synchronize_full()`;
  that is the only order between unrelated async devices.
- `dpm_prepare()` and `dpm_complete()`: never asynchronous; `dpm_list` order
  for prepare, reverse order for complete.
- `device_pm_wait_for_dev()`: the exported way for a driver to wait for a
  device it has no parent or link relation to; it returns `async_error`.
