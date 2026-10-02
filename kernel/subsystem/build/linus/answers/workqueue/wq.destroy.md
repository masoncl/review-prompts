- Outside queueing after the destroy started: the `WARN_ONCE()` in
  `__queue_work()` prints "workqueue: cannot queue %ps on wq %s"; see
  "Queueing return value" for what happens to the item and what the caller
  sees.
- `drain_workqueue()` warning: at try 10, then every 100th try up to 1000; the
  loop itself never gives up.
- Busy at the end: `WARN_ON(pwq_busy())`, `pr_warn()`, `show_pwq()`, then
  `show_one_workqueue()`; it does not call `show_all_workqueues()`.
- Leaked workqueue state after that return: sysfs entry removed, rescuer
  stopped and freed, still on the `workqueues` list, `__WQ_DESTROYING` never
  cleared, so outside queueing stays rejected.
