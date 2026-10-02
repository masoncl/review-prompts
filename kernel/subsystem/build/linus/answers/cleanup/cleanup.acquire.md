- `ACQUIRE()` and `ACQUIRE_ERR()`: both defined in
  `include/linux/cleanup.h`.
- `ACQUIRE_ERR()` after a failed trylock: `-EBUSY`, set in
  `class_##_name##_lock_err()` from `__DEFINE_GUARD_LOCK_PTR()` when the held
  value is NULL.
- `ACQUIRE_ERR()` with the base class name: works for an instance of any
  conditional class of that base, because each
  `class_##_name##_ext##_lock_err()` forwards to the base one;
  `PM_RUNTIME_ACQUIRE_ERR()` in `include/linux/pm_runtime.h` passes
  `pm_runtime_active` for all four `PM_RUNTIME_ACQUIRE()` variants, two of
  which extend `pm_runtime_active_auto`, whose class type is also
  `struct device *`.
- Wrappers that hide the pair: `PM_RUNTIME_ACQUIRE()` with
  `PM_RUNTIME_ACQUIRE_ERR()`, and `IIO_DEV_ACQUIRE_DIRECT_MODE()` with
  `IIO_DEV_ACQUIRE_FAILED()` in `include/linux/iio/iio.h`.
- `IIO_DEV_ACQUIRE_FAILED()`: is `ACQUIRE_ERR()` on a bool `_try_direct`
  class, so it yields 0 or `-EBUSY`, not a bool.
- **Potentially unsafe usage**: `ACQUIRE()` with no `ACQUIRE_ERR()` test
  before the protected data is used.
  - Unsafe: when the class is conditional; the constructor may have stored
    NULL or an error pointer and nothing else reports it.
  - Safe: when the class is unconditional and `ACQUIRE()` is used only to
    name the instance, as `ttwu_runnable()` in `kernel/sched/core.c` does
    with `__task_rq_lock`, a `DEFINE_LOCK_GUARD_1()` class in
    `kernel/sched/sched.h`, to read `guard.rq`.
  - Safe: when `ACQUIRE_ERR()` is tested and the scope is left on non-zero,
    as `commit_show()` in `drivers/cxl/core/region.c` does.
