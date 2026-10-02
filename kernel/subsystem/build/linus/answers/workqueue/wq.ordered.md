- Besides `alloc_ordered_workqueue()`, three macros also pass
  `WQ_UNBOUND | __WQ_ORDERED` and `max_active` 1:
  `alloc_ordered_workqueue_lockdep_map()` (only with `CONFIG_LOCKDEP`),
  `devm_alloc_ordered_workqueue()` and `create_singlethread_workqueue()`.

| Later change | Outcome |
|---|---|
| `workqueue_set_max_active()` | `WARN_ON()` and return |
| `workqueue_set_min_active()` | `WARN_ON()` and return |
| sysfs `max_active` file | read-only, set by `wq_sysfs_is_visible()` |
| sysfs `nice`, `cpumask`, `affinity_scope`, `affinity_strict` | let through |
| `apply_workqueue_attrs()` | let through; the only test of `__WQ_ORDERED` on the path, in `apply_wqattrs_prepare()`, sets `plugged` |
| CPU hotplug, default affinity scope change | `unbound_wq_update_pwq()` returns early |

- `apply_workqueue_attrs_locked()`: its only test of `wq->flags` is for
  `WQ_UNBOUND`; it returns `-EINVAL` when the workqueue lacks it.
- Single pwq after a change: `apply_wqattrs_prepare()` keeps one pwq only
  when the attrs passed in have `ordered` set; it does not look at
  `__WQ_ORDERED` for that.
- **Unsafe usage**: `apply_workqueue_attrs()` on an ordered workqueue with
  attrs fresh from `alloc_workqueue_attrs()`, whose `ordered` is false.
  - Unsafe: `apply_wqattrs_prepare()` then allocates one pwq per possible
    CPU, and the "ordering guarantee broken" test in `alloc_and_link_pwqs()`
    runs only at creation.
  - Safe: attrs copied from `wq->attrs`, as `wq_sysfs_prep_attrs()` does for
    the sysfs stores; `copy_workqueue_attrs()` carries `ordered` over.
