- `rpm_drop_usage_count()` in `drivers/base/power/runtime.c`: does
  `atomic_sub_return(1, &dev->power.usage_count)`; on a negative result it
  increments again, logs "Runtime PM usage count underflow!" and returns
  `-EINVAL`.
- `pm_runtime_put_noidle()`: does not call `rpm_drop_usage_count()`; it is
  `atomic_add_unless(&dev->power.usage_count, -1, 0)`, so at zero it does
  nothing, with no warning and no return value.
- Neither path leaves the counter below zero.
- An unbalanced put while another holder exists: succeeds silently on both
  paths and takes that holder's reference.
- `pm_runtime_put()` at zero: returns `void`, so the underflow shows only as
  the warning.
- `pm_runtime_allow()`: also calls `rpm_drop_usage_count()`, as
  `__pm_runtime_idle()` and `__pm_runtime_suspend()` do for the puts.
