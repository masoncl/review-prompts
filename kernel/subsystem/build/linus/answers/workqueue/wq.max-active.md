- `WQ_MAX_ACTIVE` is 2048 and `WQ_DFL_ACTIVE` is 1024, in
  `include/linux/workqueue.h`.
- There is no WQ_MAX_UNBOUND_PER_CPU and no wq_update_pwq_max_active() here;
  `wq_update_node_max_active()` in `kernel/workqueue.c` computes the limits
  of an unbound workqueue.
- Unbound workqueue: the count is per NUMA node, in
  `struct wq_node_nr_active`, shared by every pwq whose pool is on that node;
  see `pwq_tryinc_nr_active()`.
- `Documentation/core-api/workqueue.rst` says `max_active` is always a
  per-CPU attribute, even for unbound workqueues; `pwq_tryinc_nr_active()`
  counts per CPU only for per-CPU pools.
- Unbound pool not contained in one node: counted in the extra
  `NUMA_NO_NODE` slot of `wq->node_nr_active`, whose `max` is the full
  `max_active`.
- `min_active`: the floor of each node's share, not of each pwq's;
  `wq_update_node_max_active()` is the only code that applies it.
- All CPUs of an unbound workqueue offline: every node's limit becomes
  `min_active`.
- `workqueue_set_min_active()`: sets `min_active` between 0 and
  `saved_max_active`; `WARN_ON()` and return unless the workqueue is unbound,
  not ordered and not BH.
- `workqueue_set_max_active()` on an unbound workqueue: also lowers
  `saved_min_active` to the new maximum if it was higher.
