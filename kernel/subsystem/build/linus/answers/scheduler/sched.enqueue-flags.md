| Flag | Who sets it | What the class does |
|---|---|---|
| `DEQUEUE_MOVE`, `ENQUEUE_MOVE` | callers, with SAVE/RESTORE | position not kept: rt delists and re-adds (`move_entity()`); not a migration flag |
| `DEQUEUE_MIGRATING`, `ENQUEUE_MIGRATING` | only `dequeue_task_dl()` and `enqueue_task_dl()`, from `task_on_rq_migrating()` | dl moves its bandwidth as for SAVE/RESTORE |
| `ENQUEUE_MIGRATED` | `activate_task()` when `task_on_rq_migrating(p)`; `ttwu_do_activate()` for `WF_MIGRATED` | fair clears `se->exec_start` |
| `DEQUEUE_SPECIAL` | `block_task()` for `is_special_task_state()` | fair does not delay the dequeue |
| `DEQUEUE_THROTTLE` | `throttle_cfs_rq_work()`, direct call to `dequeue_task_fair()` | fair does not delay the dequeue |
| `ENQUEUE_REPLENISH` | setters, through `scope->flags`; also passed directly inside `kernel/sched/deadline.c` | dl calls `replenish_dl_entity()` |
| `ENQUEUE_RQ_SELECTED` | `ttwu_do_activate()` for `WF_RQ_SELECTED` | ext reads it as `SCX_ENQ_CPU_SELECTED` |
| `ENQUEUE_QUEUED` | `enqueue_task_fair()`, for `place_entity()` | fair-internal; no core caller passes it |

- Low 16 bits: same value on the dequeue and the enqueue side;
  `sched_change_begin()` warns on `flags & 0xFFFF0000`.
- `kernel/sched/fair.c`: tests none of `DEQUEUE_SAVE`, `ENQUEUE_RESTORE`,
  `DEQUEUE_MOVE`, `ENQUEUE_MOVE`; fair keys on `DEQUEUE_SLEEP` and
  `ENQUEUE_WAKEUP`.
- `DEQUEUE_SAVE` without `ENQUEUE_RESTORE`, core: `psi_enqueue()` and
  `sched_info_enqueue()` run with no dequeue before them.
- `DEQUEUE_SAVE` without `ENQUEUE_RESTORE`, dl: `sub_running_bw()` and
  `sub_rq_bw()` in `dequeue_dl_entity()` are not added back by
  `enqueue_dl_entity()`.
- `uclamp_rq_inc()` and `uclamp_rq_dec()`: do not test SAVE or RESTORE.
- MOVE on one side only, rt: `move_entity()` is evaluated separately on each
  side, so `WARN_ON_ONCE()` on `rt_se->on_list` fires in
  `__enqueue_rt_entity()` or `__dequeue_rt_entity()`.
- ext, dequeue without `DEQUEUE_SLEEP`: `dequeue_task_scx()` adds
  `SCX_DEQ_SCHED_CHANGE`.
- ext, `DEQUEUE_SAVE` on the current task: `dequeue_task_scx()` skips
  `scx_task_slice_ended()`; `ENQUEUE_RESTORE` on it forces the local DSQ.
- `DEQUEUE_SLEEP`: no caller passes it to a `sched_change` scope;
  `deactivate_task()` warns on it, and with it fair may return `false` and
  leave the task queued.
