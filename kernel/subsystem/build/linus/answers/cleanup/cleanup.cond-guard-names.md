- Classes defined for the five bases (`include/linux/mutex.h`,
  `include/linux/rwsem.h`, `include/linux/spinlock.h`,
  `include/linux/device.h`):

  | Base | `_try` | `_intr` | `_kill` |
  |---|---|---|---|
  | `mutex` | `mutex_try` | `mutex_intr` | `mutex_kill` |
  | `rwsem_read` | `rwsem_read_try` | `rwsem_read_intr` | none |
  | `rwsem_write` | `rwsem_write_try` | none | `rwsem_write_kill` |
  | `spinlock` | `spinlock_try` | none | none |
  | `device` | none | `device_intr` | none |

- `mutex_kill`: exists, calls `mutex_lock_killable()`.
- `rwsem_read`: no `_kill` class, although `down_read_killable()` exists.
- `device`: no `_try` class, although `device_trylock()` exists.
- `_try` is not always a trylock: `pm_runtime_active_try` and
  `pm_runtime_active_auto_try` in `include/linux/pm_runtime.h` call
  `pm_runtime_get_active()`, which resumes the device, and use `_RET == 0`;
  failure is a negative errno, not 0.
- Other suffixes in this tree: `_try_enabled` (`include/linux/pm_runtime.h`),
  `_try_direct` (`include/linux/iio/iio.h`, bool, failure 0), `_ioctl`
  (`drivers/gpu/drm/xe/xe_pm.h`, success is `_RET >= 0`).
- Conditional classes with no suffix: for example `irqdesc_lock` in
  `kernel/irq/internals.h` and `lock_timer` in `kernel/time/posix-timers.c`;
  search for `__DEFINE_CLASS_IS_CONDITIONAL` and `DEFINE_CLASS_IS_COND_GUARD`.
