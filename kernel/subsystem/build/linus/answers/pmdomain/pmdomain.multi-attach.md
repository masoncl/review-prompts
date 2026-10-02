- `dev->pm_domain` already set: `dev_pm_domain_attach_by_id()` and
  `dev_pm_domain_attach_by_name()` return `ERR_PTR(-EEXIST)`,
  `dev_pm_domain_attach_list()` returns `-EEXIST`.
- **Potentially unsafe usage**: treating every negative return of
  `dev_pm_domain_attach_list()` or `devm_pm_domain_attach_list()` as fatal.
  - Unsafe: when the device may have exactly one `power-domains` entry on a
    bus that calls `dev_pm_domain_attach()`; the bus attached it and the
    list attach returns `-EEXIST`.
  - Safe: accept `-EEXIST`, as `qcom_cc_really_probe()` does.
  - Safe: test `dev->pm_domain` first, as `imx_rproc_attach_pd()` does.
- `dev_pm_domain_attach_list()` returning 0 (no `of_node`, or no entries):
  `*list` is not written; `dev_pm_domain_detach_list()` accepts NULL.
- `genpd_dev_pm_attach_by_name()`: NULL when the name is not in
  `power-domain-names`; inside `dev_pm_domain_attach_list()` a NULL becomes
  `-ENODEV`.
- `genpd_dev_pm_attach_by_id()`: `ERR_PTR(-ENODEV)` while
  `genpd_bus_registered` is false; a missing provider gives the
  `driver_deferred_probe_check_state()` result as `ERR_PTR()`.
- `genpd_dev_pm_attach_by_id()` ends with `genpd_queue_power_off_work()`: a
  domain that was on before the attach can be powered off right after it.
- Powering through the virtual device: hold a runtime PM reference on it,
  as `qcom_pas_pds_enable()` does.
- Powering through a `DL_FLAG_PM_RUNTIME` link: the virtual device is
  resumed when the consumer runtime-resumes, see `__rpm_callback()`, and
  also on `pm_runtime_set_active()`, see `__pm_runtime_set_status()`.
- Link created with `DL_FLAG_STATELESS`: `device_link_add()` sets
  `DL_STATE_NONE` and does not resume the supplier unless
  `DL_FLAG_RPM_ACTIVE` is given, as `panfrost_pm_domain_init()` does.
