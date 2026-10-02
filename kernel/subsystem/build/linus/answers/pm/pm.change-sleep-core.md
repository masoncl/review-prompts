- `device_pm_sleep_init()`: initialises `power.completion` and calls
  `complete()` on it at once; `device_pm_init()` only calls it.
- `dpm_clear_async_state()`: reinitialises the completion in the first walk
  of each phase, under `dpm_list_mtx`, in the same walk that starts async
  work for leaf or root devices.
- Continuations: `dpm_async_resume_children()` and
  `dpm_async_suspend_parent()` take `dpm_list_mtx` before they start a
  related device, which keeps them out until that walk has ended.
- **Unsafe usage**: an exit from a `device_suspend()` or `device_resume()`
  family function that does not reach `complete_all()` on
  `power.completion`; `dpm_wait()` waits with no timeout.
  - Safe: jump to the function's `Complete` or `Out` label, as the
    `async_error` exit of `device_suspend_noirq()` does.
- **Unsafe usage**: leaving a suspend loop on error without completing the
  devices it did not reach; async work already running may wait on them.
  - Safe: call `dpm_async_suspend_complete_all()` on the source list before
    `list_splice_init()`, as `dpm_suspend()` does.
- **Unsafe usage**: leaving `device_suspend_late()` after its
  `pm_runtime_disable()` with `power.is_late_suspended` clear and runtime PM
  still disabled; `device_resume_early()` re-enables only when the flag is
  set.
  - Safe: call `pm_runtime_enable()` first, as the callback error path of
    `device_suspend_late()` does.
  - Safe: leave before `pm_runtime_disable()`, as the `async_error` and
    `pm_wakeup_pending()` exits do.
- Flags set without a callback success: `power.is_suspended` on the
  direct-complete path of `device_suspend()`; `power.is_late_suspended` and
  `power.is_noirq_suspended` at the `Skip` label.
- `power.is_prepared`: `dpm_complete()` clears it without testing it and
  calls `device_complete()` for every device on `dpm_prepared_list`;
  `device_resume()` clears it before the resume callback.
- List on failure: each suspend loop moves a device to the target list
  before handling it, so the failing device is on the target list with its
  flag clear; the devices not reached are spliced onto the same list.
- `dpm_prepare()` failure: the failing device stays on `dpm_list` without
  `power.is_prepared` and gets no `->complete()`; `device_prepare()` has
  already dropped its runtime PM reference.
