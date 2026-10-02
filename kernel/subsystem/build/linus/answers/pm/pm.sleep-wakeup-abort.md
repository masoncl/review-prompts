- Phases that check: `device_suspend()` and `device_suspend_late()` call
  `pm_wakeup_pending()`; `device_suspend_noirq()`, `device_prepare()` and
  `dpm_prepare()` do not.
- After the noirq phase: `syscore_suspend()` checks before its callbacks and
  returns `-EBUSY`; `suspend_enter()` checks again after it;
  `s2idle_enter()` checks under `s2idle_lock` each time `s2idle_loop()`
  calls it.
- `device_suspend()`: calls `pm_runtime_barrier()`, which returns void, and
  then `pm_wakeup_pending()`; it does not call `pm_wakeup_event()`.
- `device_suspend_late()`: checks before its `pm_runtime_disable()`, so an
  aborted device keeps runtime PM enabled and `power.is_late_suspended`
  clear.
- On a hit: `async_error` is set to `-EBUSY` and the local `error` stays 0;
  no device name goes to `dpm_save_failed_dev()`, but the phase still calls
  `dpm_save_failed_step()`.
- `pm_wakeup_pending()`: a hit on the event counters clears
  `events_check_enabled`, so a later call returns false unless
  `pm_abort_suspend` is positive.
- **Unsafe usage**: calling `pm_wakeup_pending()` again to learn whether the
  phase was aborted.
  - Safe: read `async_error`, as `device_suspend_late()` does before its own
    `pm_wakeup_pending()` call.
