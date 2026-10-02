- Credit callback: none in this tree. A job's `credits` change only when
  `drm_sched_can_queue()` truncates them to `credit_limit`.
- Head job does not fit: `drm_sched_rq_select_entity()` returns
  `ERR_PTR(-ENOSPC)` and `drm_sched_select_entity()` stops there. No other
  entity and no lower run queue is tried until credits come back.
- Credits during recovery: `drm_sched_stop()` subtracts the credits of every
  job it detaches from its hardware fence; `drm_sched_start()` adds the
  credits of every job on `pending_list` back.
- `timeout_wq` NULL: selects `system_percpu_wq`, not `system_wq`.
- Driver-supplied `submit_wq`: `drm_sched_init()` checks neither that it is
  ordered nor that it has `WQ_MEM_RECLAIM`.
- `drm_sched_wqueue_stop()`: runs `cancel_work_sync()` on `work_run_job` and
  `work_free_job`, so `drm_sched_stop()` and `drm_sched_fini()` wait for a
  running `run_job` or `free_job`. Those callbacks must not block on anything
  the caller of the two functions holds.
- `drm_sched_run_job_queue()` and `drm_sched_run_free_queue()`: queue nothing
  while `pause_submit` is set.
