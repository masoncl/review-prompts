- `drm_sched_job_init()`: fails only with `-EINVAL` for zero credits and
  `-ENOMEM` for the fence allocation. It tests neither `entity` nor
  `entity->rq`, and does not return `-ENOENT`, although its kerneldoc says so.
- `drm_sched_job_arm()`: does `BUG_ON(!entity)` and then dereferences
  `entity->rq`, which `drm_sched_entity_select_rq()` sets to NULL when
  `drm_sched_pick_best()` finds no ready scheduler.
- `drm_sched_entity_push_job()` on a killed entity: cannot report it.
  `drm_sched_rq_add_entity()` logs "Trying to push to a killed entity" after
  the job is already in `job_queue`; the job stays there until the next
  `drm_sched_entity_kill()`, for example from `drm_sched_entity_fini()`,
  finishes it with `-ESRCH`.
- After `drm_sched_entity_push_job()` returns: the job may already be freed.
  Take what is needed between arm and push, as `panfrost_job_push()` does
  with `s_fence->finished`.
