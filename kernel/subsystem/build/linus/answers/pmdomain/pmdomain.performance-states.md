- Powered-off subdomain: its `link->performance_state` still counts;
  `_genpd_reeval_performance_state()` tests no status, and neither
  `genpd_power_off()` nor `genpd_sync_power_off()` writes the link field.
- Runtime-suspended device: its vote is zeroed by
  `genpd_drop_performance_state()`, not by
  `genpd_dev_pm_set_performance_state()`.
- `genpd_dev_pm_set_performance_state()` on a `pm_runtime_suspended()` device:
  only stores the value in `rpm_pstate`; the domain is not changed until
  resume.
- Device suspended by system sleep and not runtime suspended: keeps its vote;
  `genpd_finish_suspend()` does not touch performance states.
- Translation to a parent: there is no parent_performance_state field;
  `genpd_xlate_performance_state()` does it.
- Parent without `set_performance_state`: `genpd_xlate_performance_state()`
  passes the child's state through untranslated.
- Domain without `set_performance_state`: still records
  `genpd->performance_state` and still propagates to its parents.
- Several parents: `_genpd_set_performance_state()` walks `child_links` forward
  when the state goes up and in reverse when it goes down;
  `_genpd_set_parent_state()` handles one link.
