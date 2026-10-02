- State sampled for the elapsed interval: `__update_load_avg_cfs_rq()` reads
  `cfs_rq->load.weight`, `cfs_rq->h_nr_runnable` and `cfs_rq->h_curr`;
  `__update_load_avg_se()` reads `se->on_rq`, `se_runnable()` and
  `cfs_rq->h_curr == se`.
- A change of `h_curr` or `h_nr_runnable` therefore needs the update first
  too; `set_next_entity()` and `put_prev_entity()` do so, and
  `__dequeue_task()` does so before `set_delayed()` for the task's own
  level only.
- `dequeue_entity()` order: `update_load_avg()`, `se_update_runnable()`,
  `account_entity_dequeue()`, then `update_cfs_group()`; `enqueue_entity()`
  calls `update_cfs_group()` before `account_entity_enqueue()`.
- `update_curr()`: not called by `enqueue_entity()` or `dequeue_entity()`;
  `enqueue_hierarchy()` and `dequeue_hierarchy()` call it per level first.
- Ancestor levels: updated by the loops in `enqueue_hierarchy()` and
  `dequeue_hierarchy()`.
- `UPDATE_UTIL_EST`: a fifth flag; `dequeue_entity()` passes it for a task
  going to sleep (`DEQUEUE_SLEEP` without `DEQUEUE_DELAYED`) and
  `__dequeue_task()` when it delays the dequeue.
- `cfs_rq->pelt_clock_throttled`: the only state that freezes
  `cfs_rq_clock_pelt()`; it is set for a runqueue in a throttled hierarchy
  only while `nr_queued` is 0.
- A throttled runqueue that still has entities queued: its PELT clock keeps
  advancing; see `tg_throttle_down()` and the end of `dequeue_entity()`.
- `enqueue_entity()` on the first entity and `tg_unthrottle_up()`: restart
  the clock and add the frozen span to `throttled_clock_pelt_time`.
- Idle CPU: `update_rq_clock_pelt()` sets `rq->clock_pelt` to
  `rq_clock_task()`; the clock does not stall.
