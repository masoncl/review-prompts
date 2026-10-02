- `drm_sched_entity_kill()`: exported and declared in
  `include/drm/gpu_scheduler.h`, not static. Use it instead of a flush when
  queued jobs should not be waited for.
- `drm_sched_entity_flush()` timeout: used only when the caller has
  `PF_EXITING`. Otherwise it uses `wait_event_killable()` with no time bound
  and returns `timeout` unchanged.
- `drm_sched_entity_flush()` waits for `drm_sched_entity_is_idle()`: the job
  queue is empty, or the entity is stopped or off its run queue. It does not
  wait for jobs to finish on the hardware.
- `drm_sched_entity_flush()` kills only when the caller's thread group leader
  is the entity's `last_user`, the caller has `PF_EXITING`, and its exit code
  is `SIGKILL`.
- `drm_sched_entity_kill()` does not wait for the killed jobs to be freed.
  Each job is finished and passed to `free_job` from
  `drm_sched_entity_kill_jobs_work()`, queued with `schedule_work()` once the
  previous job and the dependencies have signalled.
- `drm_sched_fini()` and entities: it does not mark entities stopped or take
  them off the run queues. It frees each run queue with `kfree()`.
- `drm_sched_fini()` stops work with `drm_sched_wqueue_stop()`; the kerneldoc
  of `drm_sched_stop()` says not to use that one for teardown.
- `drm_sched_fini()` warning: "Tearing down scheduler while jobs are
  pending!" prints only if `pending_list` is not empty at the end, so not
  after `cancel_job` ran.
- **Potentially unsafe usage**: calling `drm_sched_fini()` while an entity is
  still attached to the scheduler.
  - Unsafe: when a job was pushed to the entity, or the entity is later
    passed to `drm_sched_entity_flush()` or `drm_sched_entity_destroy()`;
    `entity->rq` then points to freed memory; `drm_sched_entity_flush()`
    reads `entity->rq->sched`, and `drm_sched_entity_kill()` takes `rq->lock`
    for an entity on the list.
  - Safe: `drm_sched_entity_fini()` afterwards on an entity that never had a
    job pushed, as `pvr_queue_destroy()` does on the context creation failure
    path; `drm_sched_rq_remove_entity()` returns on
    `list_empty(&entity->list)` before it touches the run queue.
  - Safe: finish every entity first, then the scheduler, then destroy a
    driver-owned `submit_wq`, as `nouveau_sched_fini()` does.
