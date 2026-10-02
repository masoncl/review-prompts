- `drm_sched_job_timedout()`: tests the return value only against
  `DRM_GPU_SCHED_STAT_NO_HANG` and `DRM_GPU_SCHED_STAT_ENODEV`.
  `DRM_GPU_SCHED_STAT_NONE` takes the same path as
  `DRM_GPU_SCHED_STAT_RESET`.
- `DRM_GPU_SCHED_STAT_RESET`: the scheduler re-arms the timer and does not put
  the job back on `pending_list`. Only `drm_sched_stop()` with the job as
  `bad` puts it back.
- Handler that returns RESET without `drm_sched_stop()` on the job: the
  scheduler never calls `free_job` for it; the handler frees it, as
  `mock_sched_timedout_job()` does.
- `DRM_GPU_SCHED_STAT_NO_HANG`: handled by
  `drm_sched_job_reinsert_on_false_timeout()`, which does the same
  `list_add()` as `drm_sched_stop()` does for `bad`; both for one job adds it
  twice.
- `free_guilty`: when `drm_sched_stop()` set it, `free_job` runs on the job
  after the callback, whatever the callback returned.
- `drm_sched_stop()`: drops the parent reference and sets `s_fence->parent` to
  NULL for every job it detaches.
- `drm_sched_start()`: finishes each job without a parent with
  `errno ?: -ECANCELED`. After `drm_sched_stop()` that is every remaining job,
  unless something set the parent again, as `drm_sched_resubmit_jobs()` does.
- `drm_sched_start()` with errno 0: the remaining jobs still end with
  `-ECANCELED`.
- Recovery sequences: stated only in the kerneldoc of `timedout_job` in
  `include/drm/gpu_scheduler.h`; no code enforces them.
  - Firmware scheduler: `drm_sched_stop()`, remove the ring, kill the entity
    and its scheduler. There is no `drm_sched_start()` step.
  - Hardware scheduler: `drm_sched_stop()` on all affected schedulers, kill
    the entity of the faulty job, reset, resubmit to live entities,
    `drm_sched_start()`.
- Deprecated: `drm_sched_resubmit_jobs()` (kerneldoc in `sched_main.c`) and
  `hang_limit` (kerneldoc of `struct drm_sched_init_args`). In-tree drivers
  still call the first.
- `drm_sched_increase_karma()`: carries no deprecation note.
- Not in this tree: drm_sched_resubmit_jobs_ext and drm_sched_job_recovery.
- Replacement named by the kerneldoc: `drm_sched_for_each_pending_job()` after
  stopping the scheduler. It and `drm_sched_job_is_signaled()` do `WARN_ON()`
  unless `drm_sched_is_stopped()` is true.
