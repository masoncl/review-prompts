| Function | Skips the callback when |
|---|---|
| `pm_runtime_force_suspend()` | status is `RPM_SUSPENDED`, or `power.needs_force_resume` is already set |
| `pm_runtime_force_resume()` | `power.needs_force_resume` is clear and (`dev_pm_smart_suspend()` is false or status is `RPM_SUSPENDED`) |

- `pm_runtime_force_resume()`: makes no test of whether runtime PM is enabled,
  and does not set the status on success.
- `pm_runtime_force_suspend()`: tests `power.runtime_status`, not the
  hardware; a powered device still at the `RPM_SUSPENDED` that
  `pm_runtime_init()` sets gets no callback.
- Configuration: `pm_runtime_force_suspend()` is built with `CONFIG_PM`, and
  its stub returns 0; `pm_runtime_force_resume()` needs `CONFIG_PM_SLEEP`, and
  its stub returns `-ENXIO`.
- Outside system sleep: `pm_runtime_force_suspend()` is also called from
  remove callbacks, for example `sdhci_omap_remove()`; `pm_runtime_reinit()`
  clears `power.needs_force_resume` for that case.
- **Unsafe usage**: a system suspend callback that returns 0 after
  `pm_runtime_force_suspend()` when nothing in the resume path re-enables
  runtime PM; it stays disabled.
  - Safe: `pm_runtime_force_resume()` as the resume callback of the same
    phase, as `DEFINE_RUNTIME_DEV_PM_OPS()` does; it ends with
    `pm_runtime_enable()` on every path.
  - Safe: no undo when `pm_runtime_force_suspend()` itself returns an error;
    it has already called `pm_runtime_enable()`.
- **Potentially unsafe usage**: a suspend callback that returns an error after
  `pm_runtime_force_suspend()` succeeded.
  - Unsafe: when it returns without undoing; the PM core runs no resume
    callback of that phase for the device (`power.is_suspended`,
    `power.is_late_suspended` or `power.is_noirq_suspended` stays clear), so
    runtime PM stays disabled.
  - Safe: call `pm_runtime_force_resume()` before returning the error, as
    `renesas_sdhi_suspend()` does.
- **Potentially unsafe usage**: register access in the resume callback right
  after `pm_runtime_force_resume()` returns 0.
  - Unsafe: when the status was already `RPM_SUSPENDED` at force suspend, or
    `pm_runtime_need_not_resume()` was true there, that is usage count at
    most 1 and no counted active children; `power.needs_force_resume` is
    clear, the callback is skipped as the table says and the device stays
    `RPM_SUSPENDED`.
  - Safe: when the driver resumes the device and holds its own usage
    reference across the pair, as `sdhci_esdhc_suspend()` takes with
    `pm_runtime_resume_and_get()` and `sdhci_esdhc_resume()` drops;
    `pm_runtime_need_not_resume()` is then false.
