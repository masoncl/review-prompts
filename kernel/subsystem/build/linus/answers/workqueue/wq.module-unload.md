- `flush_scheduled_work()`: still a macro in `include/linux/workqueue.h`; it
  calls `__warn_flushing_systemwide_wq()` and then flushes `system_percpu_wq`.
  No in-tree code calls it.
- What the tree says: the header comments state no reason themselves; they
  say to stop using `flush_scheduled_work()`, that it will be removed, and
  link to a mailing-list message for the reasons and the steps of converting
  to local workqueues.
