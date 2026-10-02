- `scoped_cond_guard()`: present in `include/linux/cleanup.h`; only for
  conditional classes, its fail branch holds
  `BUILD_BUG_ON(!__is_cond_ptr(_name))`.
- `scoped_cond_guard()` whose fail statement does not leave (an assignment):
  the body is skipped and execution continues after the block, as in
  `margining_eye_write()` in `drivers/thunderbolt/debugfs.c`.
- `ACQUIRE_ERR()` on failure: returns `-EBUSY` when the class uses the
  default success test (for example `mutex_try`); for classes defined with
  `_RET == 0` it returns the negative errno that the lock function returned.
- Networking code: `Documentation/process/maintainer-netdev.rst` discourages
  `guard()` in a function longer than 20 lines, prefers `scoped_guard()`, and
  weakly prefers plain lock and unlock over both.
