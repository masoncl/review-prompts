- `rpm_resume()` on `RPM_RESUMING` with `RPM_ASYNC` or `RPM_NOWAIT`:
  `-EINPROGRESS`.
- `rpm_resume()` on `RPM_SUSPENDING` with `RPM_NOWAIT`: sets
  `power.deferred_resume` and returns `-EINPROGRESS`.
- `rpm_resume()` on `RPM_SUSPENDING` with `RPM_ASYNC` and no `RPM_NOWAIT`:
  sets `power.deferred_resume` and returns `0`.
- `rpm_suspend()` on `RPM_RESUMING` without `RPM_ASYNC`: `-EAGAIN`, no wait;
  `RPM_NOWAIT` alone gets this too.
- `rpm_suspend()` on `RPM_RESUMING` with `RPM_ASYNC`: goes on to arm the timer
  or queue the request and returns `0`.
- `rpm_check_suspend_allowed()`: runs before any of the `rpm_suspend()` cases,
  so a held reference gives `-EAGAIN` first.
- Sync `rpm_suspend()` on `RPM_SUSPENDING` with `power.deferred_resume` set:
  `-EAGAIN` from the check, no wait.
- `power.irq_safe` devices: the wait is a loop of unlock, `cpu_relax()`, lock,
  not a sleep on `power.wait_queue`.
- `pm_runtime_work()`: passes `RPM_NOWAIT` for every request type, so a queued
  request that finds the device `RPM_SUSPENDING` or `RPM_RESUMING` returns
  instead of waiting.
- Deferred resume after a successful callback: `rpm_suspend()` first sets
  `RPM_SUSPENDED`, drops the parent's `power.child_count` and wakes waiters,
  then calls `rpm_resume(dev, 0)`.
- `-EAGAIN` from that path: the result of `rpm_resume(dev, 0)` is discarded,
  so `-EAGAIN` does not prove the device is active.
- Failed suspend callback: the `fail:` label clears `power.deferred_resume`
  without resuming; the status is already back to `RPM_ACTIVE`.
