- Handler: `mock_sched_timedout_job()`; there is no
  drm_mock_sched_job_timedout.
- Flags: `DRM_MOCK_SCHED_JOB_DONE`, `DRM_MOCK_SCHED_JOB_TIMEDOUT`,
  `DRM_MOCK_SCHED_JOB_DONT_RESET` and `DRM_MOCK_SCHED_JOB_RESET_SKIPPED`, in
  `drivers/gpu/drm/scheduler/tests/sched_tests.h`. `flags` is a plain
  `unsigned long`.
- Repeat runs: happen only for a job with `DRM_MOCK_SCHED_JOB_DONT_RESET`,
  where the handler returns `DRM_GPU_SCHED_STAT_NO_HANG`.
- `drm_sched_skip_reset()` in
  `drivers/gpu/drm/scheduler/tests/tests_basic.c`: waits `2 * MOCK_TIMEOUT` on
  a scheduler whose timeout is `MOCK_TIMEOUT`, so the handler can run twice
  before the test looks at the flags.
- Reset path: runs at most once per job. The handler returns
  `DRM_GPU_SCHED_STAT_RESET` without `drm_sched_stop()`, so the job never
  returns to `pending_list`.
- Reset path cleanup: the handler drops the `hw_fence` reference and calls
  `drm_sched_job_cleanup()` itself, because `free_job` will not be called.
- `DRM_MOCK_SCHED_JOB_DONE` and `DRM_MOCK_SCHED_JOB_TIMEDOUT`: set under
  `lock` of `struct drm_mock_scheduler`. The tests read `flags` without it.
- **Unsafe usage**: clearing `DRM_MOCK_SCHED_JOB_DONT_RESET` in the handler.
  - Unsafe: the next run for the same job takes the reset path, signals
    `hw_fence` with `-ETIMEDOUT` and cleans the job up, while the test still
    expects `drm_mock_sched_advance()` to complete it.
  - Safe: leave the request flag set and OR in
    `DRM_MOCK_SCHED_JOB_RESET_SKIPPED`, as `mock_sched_timedout_job()` does;
    `drm_sched_skip_reset()` asserts on that flag.
