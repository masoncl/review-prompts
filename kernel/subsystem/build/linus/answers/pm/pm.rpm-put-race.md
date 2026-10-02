- `pm_runtime_put_sync()`: the put helper that returns the `rpm_idle()`
  result; in this race it returns `-EAGAIN`, unfiltered.
- `-EAGAIN` from a put: also returned for a pending resume request, a status
  of `RPM_SUSPENDING` or `RPM_RESUMING`, or a transient callback result; the
  value does not identify the race.
- `-EINVAL` from a put: usage counter underflow, `power.runtime_error` set,
  or a callback returning it; the value does not tell which.
- Repeating a put after `-EAGAIN`: while another holder exists it drops that
  holder's reference and can suspend the device under it.
