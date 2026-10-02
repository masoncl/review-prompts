- `genpd_power_off()` in `drivers/pmdomain/core.c`: returns `void`; every
  decline is a bare `return`, no `-EBUSY` or `-EAGAIN` reaches a caller.
- Conditions that make it return before the provider is called, in order:
  1. `!genpd_status_on(genpd)`
  2. `genpd->prepared_count > 0`
  3. `GENPD_FLAG_ALWAYS_ON` or `GENPD_FLAG_RPM_ALWAYS_ON`
  4. `genpd->stay_on`
  5. `atomic_read(&genpd->sd_count) > 0`
  6. a subdomain on `parent_links` with
     `child->state_idx < child->state_count - 1`
  7. a device on `dev_list` with `rpm_always_on` set in its
     `struct generic_pm_domain_data` (set by `dev_pm_genpd_rpm_always_on()`)
  8. more than one device counted as not suspended, or one when `one_dev_on`
     is false; a device counts when `pm_runtime_suspended()` is false or
     `irq_safe_dev_in_sleep_domain()` is true
  9. `genpd->gov->power_down_ok()` returns false
  10. `sd_count > 0` again, after the governor
- `GENPD_FLAG_ACTIVE_WAKEUP`, `device_may_wakeup()` and `device_awake_path()`:
  not tested by `genpd_power_off()`.
- Governor with no `power_down_ok`: `genpd->state_idx` keeps its last value;
  it is reset to 0 only when `genpd->gov` is NULL.
- Declines 1 to 10: counted nowhere; `genpd->status` is not changed.
- Provider refusal: `_genpd_power_off()` returns non-zero both for a
  `GENPD_NOTIFY_PRE_OFF` notifier veto and for a `genpd->power_off()` error.
- On provider refusal: `genpd_power_off()` increments `rejected` of
  `genpd->states[genpd->state_idx]`, discards the error code, leaves the status
  on and does not touch the parents.
- `rejected`: readable in the debugfs file `idle_states`, printed by
  `idle_states_show()`.
- Callers in `drivers/pmdomain/core.c`: none reads `genpd->status` after the
  call; `genpd_runtime_suspend()` returns 0 whether or not the domain went
  off.
- Consumer that needs the outcome: `dev_pm_genpd_is_on()`, or a notifier from
  `dev_pm_genpd_add_notifier()`; `_genpd_power_off()` sends `GENPD_NOTIFY_OFF`
  only on success, `GENPD_NOTIFY_ON` follows a failed `genpd->power_off()`.
