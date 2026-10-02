- `rpm_idle()`: does not wait for a running idle notification; with
  `idle_notification` set it returns `-EINPROGRESS`.
- Waiter for `idle_notification`: only `__pm_runtime_barrier()`.
- `rpm_suspend()`: waits only for `RPM_SUSPENDING`; a synchronous call in
  `RPM_RESUMING` returns `-EAGAIN`.
- `no_callbacks` device: `rpm_suspend()` and `rpm_resume()` set the settled
  status directly; `RPM_SUSPENDING` and `RPM_RESUMING` are never visible.
- `power.lock` is also dropped in settled states: in `rpm_resume()` while the
  parent resumes (child `RPM_SUSPENDED`) and for `pm_runtime_put()` on the
  parent; in `rpm_suspend()` after `RPM_SUSPENDED` for the parent and
  suppliers.
- Test: `drivers/base/power/runtime-test.c`, built with
  `CONFIG_PM_RUNTIME_KUNIT_TEST`, suite `pm_runtime_test_cases`.
- The test calls the wrappers in `include/linux/pm_runtime.h` on a device
  from `kunit_device_register()`, which has no runtime PM callbacks.
- Return values the test expects: 0, 1, `-EAGAIN`, `-EACCES` and `-EINVAL`.
- Not covered by the test: `-EBUSY`, `-EINPROGRESS`, callback errors,
  `irq_safe`, and concurrent callers.
