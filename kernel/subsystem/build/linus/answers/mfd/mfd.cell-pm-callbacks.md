- `suspend` and `resume` in `struct mfd_cell`: both are declared in
  `include/linux/mfd/core.h`, as `int (*)(struct platform_device *)`.
- No cell in this tree sets either member, and nothing reads or calls them;
  `drivers/mfd/mfd-core.c` only copies them with the rest of the cell.
- **Unsafe usage**: setting `suspend` or `resume` in a `struct mfd_cell` and
  expecting it to run over system sleep.
  - Safe: put the callbacks in the child driver's `dev_pm_ops`, as
    `dln2_spi_pm` in `drivers/spi/spi-dln2.c` does; `platform_pm_suspend()`
    and `platform_pm_resume()` in `drivers/base/platform.c` call those.
- Child callbacks come from the platform bus when the child has no
  `pm_domain`: `mfd_dev_type` has no `pm`, so `device_suspend()` falls
  through to `platform_dev_pm_ops`. A child with `dev->pm_domain` set gets
  the callbacks of the domain instead.
- A child driver with no `dev_pm_ops` gets the legacy `suspend` and `resume`
  of `struct platform_driver` instead, see `platform_legacy_suspend()`.

| Phase | Order | Where |
|---|---|---|
| `prepare` | parent, then children | `dpm_prepare()` |
| `suspend`, `suspend_late`, `suspend_noirq` | children, then parent | `dpm_suspend()`, `dpm_suspend_late()`, `dpm_noirq_suspend_devices()` |
| `resume_noirq`, `resume_early`, `resume` | parent, then children | `dpm_noirq_resume_devices()`, `dpm_resume_early()`, `dpm_resume()` |
| `complete` | children, then parent | `dpm_complete()` |

- Sibling order in `dpm_list`: starts as cell array order, but a child whose
  probe is retried after deferral is moved to the tail of `dpm_list` by
  `device_pm_move_to_tail()`, called from `deferred_probe_work_func()`.
- Async: neither `mfd_add_device()` nor `platform_device_add()` calls
  `device_enable_async_suspend()`, so a child is handled synchronously unless
  its driver calls it or, with `CONFIG_PM_ADVANCED_DEBUG`, the `async` sysfs
  attribute enables it.
- With async enabled the parent/child order still holds, through
  `dpm_wait_for_subordinate()` on suspend and `dpm_wait_for_superior()` on
  resume; sibling order does not.
