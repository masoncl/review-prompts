- `nr_queued`: entities accounted at this level by `account_entity_enqueue()`
  (tasks and group entities with this `cfs_rq_of()`); on `rq->cfs` it is not
  the size of the rbtree.
- `rq->cfs.h_nr_queued`: the number of tasks competing in the tree, `curr`
  and delayed tasks included.
- "Anything to pick" and "only one task": test `rq->cfs.h_nr_queued`, as
  `pick_task_fair()`, `pick_eevdf()` and `update_curr()` do.
- First or last entity of a level: test `nr_queued`, as `enqueue_entity()`,
  `dequeue_entity()` and `tg_throttle_down()` do.
- `sched_fair_runnable()`: tests `rq->cfs.nr_queued > 0`; valid for
  emptiness only, not for a count of tasks.
- `place_entity()`: reads `h_nr_queued` as the number of other tasks; a
  caller that already counted the entity passes `ENQUEUE_QUEUED` or lowers
  the counter around the call, as `requeue_delayed_entity()` does.
- `sched_idle_rq()`: compares `rq->nr_running` with `rq->cfs.h_nr_idle`.
- Counter walks: `enqueue_hierarchy()`, `dequeue_hierarchy()`,
  `set_delayed()` and `clear_delayed()` go to the root; none stops at a
  throttled level.
- A throttled task on a limbo list: in none of the four counters and not in
  `rq->nr_running`.
- Delayed tasks: no counter field; `cfs_h_nr_delayed()` returns
  `h_nr_queued - h_nr_runnable` of `rq->cfs`.
