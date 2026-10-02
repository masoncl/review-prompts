- `struct drm_sched_backend_ops`: five members, `prepare_job`, `run_job`,
  `timedout_job`, `free_job`, `cancel_job`. There is no update_job_credits
  callback in this tree.
- NULL tests: the scheduler tests only `prepare_job` and `cancel_job` for NULL.
- `free_job`: required even with `cancel_job`;
  `drm_sched_cancel_remaining_jobs()` calls `free_job` right after
  `cancel_job`.
- `free_job` contexts: not only `submit_wq`.

  | Caller | Context |
  |---|---|
  | `drm_sched_free_job_work()` | `submit_wq` |
  | `drm_sched_stop()` | its caller, for example the timeout handler |
  | `drm_sched_job_timedout()`, when `free_guilty` is set | `timeout_wq` |
  | `drm_sched_cancel_remaining_jobs()` | caller of `drm_sched_fini()` |
  | `drm_sched_entity_kill_jobs_work()` | work queued by `schedule_work()` |

- `free_job` from the kill path: the job never ran, so `s_fence->parent` is
  NULL and `run_job` was never called for it.
- `run_job` returning NULL: the job is finished at once with result 0, which
  sets no error on the finished fence; an `ERR_PTR()` sets its errno.
- `run_job` fence reference: `drm_sched_run_job_work()` drops the returned
  reference as soon as the completion callback is added.
  `drm_sched_fence_set_parent()` takes a separate reference for
  `s_fence->parent`.
- `run_job` second call: from the scheduler only through
  `drm_sched_resubmit_jobs()`, in the context of its caller; a driver can
  also call `ops->run_job` itself, as `xe_sched_resubmit_jobs()` does.
- `prepare_job`: called from `drm_sched_job_dependency()` once the job's
  `dependencies` are used up, and called again until it returns NULL.
  `drm_sched_entity_kill()` does not call it for the jobs it pops.
- `cancel_job`: called for each job on `pending_list`, newest first. Those
  jobs were all passed to `run_job` already; the kerneldoc's "have not been
  executed" does not match `drm_sched_cancel_remaining_jobs()`.
- `cancel_job` implementations: only `mock_sched_cancel_job()` in
  `drivers/gpu/drm/scheduler/tests/mock_scheduler.c`; no driver sets it.
- **Potentially unsafe usage**: leaving `timedout_job` NULL.
  - Unsafe: when `work_tdr` can run with a job on `pending_list`;
    `drm_sched_job_timedout()` calls the pointer with no NULL test. A finite
    `timeout`, `drm_sched_fault()`, `drm_sched_tdr_queue_imm()` and
    `drm_sched_resume_timeout()` all queue that work.
  - Safe: with `timeout` set to `MAX_SCHEDULE_TIMEOUT` and none of those
    calls, as `msm_ringbuffer_new()` sets up; `drm_sched_start_timeout()`
    then never queues `work_tdr`.
