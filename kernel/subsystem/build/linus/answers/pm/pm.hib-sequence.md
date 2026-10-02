- Success path: models have the five stages, messages and callbacks right;
  see `hibernation_snapshot()`, `create_image()`,
  `hibernation_platform_enter()` and `hibernation_restore()` in
  `kernel/power/hibernate.c`.
- Message after a failure in the hibernating kernel: chosen by
  `in_suspend ? (error ? PMSG_RECOVER : PMSG_THAW) : PMSG_RESTORE`;
  `in_suspend` is set to 1 only just before `swsusp_arch_suspend()`, so
  with `in_suspend` 0 on entry earlier failures give `PMSG_RESTORE`, not
  `PMSG_RECOVER`.

| Failure point | What the core sends next |
|---|---|
| `dpm_prepare(PMSG_FREEZE)`, `hibernate_preallocate_memory()` or `freeze_kernel_threads()` | `dpm_complete(PMSG_RECOVER)` only: `->complete`, no thaw callback |
| `dpm_suspend(PMSG_FREEZE)` | `dpm_resume()` and `dpm_complete()` with `PMSG_RESTORE`: `->restore`, `->complete` |
| late or noirq freeze, inside `dpm_suspend_end(PMSG_FREEZE)` | the phase unwinds itself with `PMSG_RECOVER`, then `hibernation_snapshot()` sends `PMSG_RESTORE` |
| `platform_pre_snapshot()`, `pm_sleep_disable_secondary_cpus()`, `syscore_suspend()` or a pending wakeup in `create_image()` | `PMSG_RESTORE` for the noirq, early and main phases |
| `swsusp_arch_suspend()` returns an error | `PMSG_RECOVER` for all three phases |
| `swsusp_write()` | nothing; devices stay as the thaw left them |
| `hibernation_platform_enter()`, after `hibernation_ops->begin()` succeeded | `PMSG_RESTORE` |

- Late or noirq freeze failure: a driver can therefore see `->thaw_noirq`
  or `->thaw_early` followed by `->restore`.
- `power_down()` after `hibernation_platform_enter()` fails: `-EAGAIN` or
  `-EBUSY` rolls back and the system keeps running; any other error falls
  through to `kernel_power_off()` or `kernel_halt()`, so drivers then see
  `->shutdown`.
- `PMSG_HIBERNATE`: sent only by `hibernation_platform_enter()`, which
  `hibernate()` reaches only in `HIBERNATION_PLATFORM` mode;
  `hibernation_mode` starts as `HIBERNATION_SHUTDOWN` and becomes platform
  mode when `hibernation_set_ops()` installs ops, and `power_down()`
  switches to it after a failed `HIBERNATION_SUSPEND` when ops are
  installed.
- `HIBERNATION_TEST_RESUME` mode: no power-off; after the image is written
  `hibernate()` calls `load_image_and_restore()` in the same kernel, so
  drivers see `PMSG_QUIESCE` and then `PMSG_RESTORE`.
- `PMSG_POWEROFF`: defined in `include/linux/pm.h` and mapped to the
  poweroff callbacks by `pm_op()`, but nothing in this tree sends it.
