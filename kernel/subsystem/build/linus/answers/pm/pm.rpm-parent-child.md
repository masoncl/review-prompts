- `rpm_resume()` of a child: resumes the parent with `rpm_resume(parent, 0)`,
  which is synchronous; `RPM_ASYNC` is not passed on.
- Child status while the parent resumes: still `RPM_SUSPENDED`, with the
  child's `power.lock` dropped; `RPM_RESUMING` is set only afterwards.
- `rpm_resume()` returns `-EBUSY` when the parent is not `RPM_ACTIVE` after
  that call; this is the one error value that comes from the parent.
- On that `-EBUSY`: the parent's own error code is dropped, and the child's
  `runtime_status` and `runtime_error` are unchanged.
- `-EBUSY` from `rpm_resume()` can also be the return value of the child's
  `->runtime_resume()` callback, which `rpm_callback()` passes through.
- `rpm_suspend()`: no return value depends on the parent; its `-EBUSY` from
  `rpm_check_suspend_allowed()` is about the device's own `child_count`.
- No `-EAGAIN` and no `-EINVAL` comes from the parent's state.
- Parent with `disable_depth` non-zero: not resumed and its status not
  tested; the child's resume goes on whatever the parent's status is.
- `RPM_ASYNC` resume of a suspended child: queues the request and returns 0
  without resuming the parent, unless the `no_callbacks` shortcut applies.
- `no_callbacks` shortcut in `rpm_resume()`: applies when the parent is
  disabled, has `ignore_children` set or is `RPM_ACTIVE`; it runs before the
  `RPM_ASYNC` test, so `pm_request_resume()` makes such a child `RPM_ACTIVE`
  at once and returns 1.
