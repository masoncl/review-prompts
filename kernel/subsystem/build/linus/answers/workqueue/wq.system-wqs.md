- All twelve are created at the end of `workqueue_init_early()` in
  `kernel/workqueue.c`; the rows below are the ones easy to get wrong.

| Pointer | Name string | Kind | Use |
|---|---|---|---|
| `system_dfl_long_wq` | "events_dfl_long" | unbound, `WQ_MAX_ACTIVE` | unbound items that may run long |
| `system_freezable_power_efficient_wq` | "events_freezable_pwr_efficient" | per-CPU or unbound | freezable and power-efficient |
| `system_wq` | "events" | per-CPU | deprecated; use `system_percpu_wq` |
| `system_unbound_wq` | "events_unbound" | unbound | deprecated; use `system_dfl_wq` |

- `system_wq` and `system_unbound_wq`: each is its own
  `struct workqueue_struct`, not an alias; it shares the name string and
  the worker pools with its replacement.
- Flushing `system_percpu_wq` does not wait for items queued on `system_wq`,
  and the same holds for the unbound pair.
- Queueing on a deprecated one: `__queue_work()` tests `__WQ_DEPRECATED` and
  calls `pr_warn_once()`, then queues the item normally.
- That `pr_warn_once()` is one call site, so only the first such item in a
  boot is reported, whichever of the two workqueues it used.
- `schedule_work()`, `schedule_work_on()`, `schedule_delayed_work()` and
  `schedule_delayed_work_on()`: all queue on `system_percpu_wq`.
