- `lock_system_sleep()` return value: the whole of `current->flags` from
  before the call, not a boolean; `unlock_system_sleep()` tests
  `PF_NOFREEZE` in it.
- `system_transition_mutex` and the `reboot` syscall: the syscall in
  `kernel/reboot.c` holds it with plain `mutex_lock()` while it runs the
  command, so restart, power-off and `kernel_kexec()` are excluded too.
- Takers that fail with `-EBUSY` instead of waiting: `enter_state()`,
  `snapshot_ioctl()` and `hibernate_compressor_param_set()` use
  `mutex_trylock()`.
- `software_resume()`: takes `system_transition_mutex` with plain
  `mutex_lock()`, without setting `PF_NOFREEZE`.
- `hibernate_acquire()` in `kernel/power/hibernate.c`: every caller, for
  example `hibernate()` and `snapshot_open()`, calls it with
  `system_transition_mutex` already held.
- `hibernate_acquire()` versus the mutex: `/dev/snapshot` keeps the claim
  from `snapshot_open()` to `snapshot_release()`, while
  `system_transition_mutex` is dropped between the file operations.
- `device_pm_lock()`: the wrapper for code outside
  `drivers/base/power/main.c`, for example `device_move()` and
  `device_pm_move_to_tail()` in `drivers/base/core.c`; `device_pm_add()`,
  `device_pm_remove()` and the `dpm_*` phase functions take `dpm_list_mtx`
  directly.
- `dpm_suspend_start()` and `dpm_resume_end()`: call
  `pm_restrict_gfp_mask()` and `pm_restore_gfp_mask()`, which warn unless
  `system_transition_mutex` is locked; a caller outside `kernel/power/`
  needs it held, and `do_suspend()` in `drivers/xen/manage.c` takes it
  first.
