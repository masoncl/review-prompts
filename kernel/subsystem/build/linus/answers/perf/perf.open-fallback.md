- `evsel__detect_missing_features()`: called only from `evsel__open_cpu()`, at
  `try_fallback`, and only when `err == -EINVAL`.
- Order at `try_fallback`: `evsel__ignore_missing_thread()`, then the
  `-EMFILE` rlimit retry, then the detection, then
  `evsel__precise_ip_fallback()`.
- A true return: `goto fallback_missing_features`, not `retry_open`; that
  label reruns `evsel__disable_missing_features()` and restarts the open loop
  at `start_cpu_map_idx`.
- Generic probes: use a scratch attr (software task-clock, disabled), never
  the evsel's attr; the evsel's attr is edited by
  `evsel__disable_missing_features()`, not by the probes.
- Run-once state: a separate static `detection_done` in each of
  `evsel__detect_missing_features()`,
  `evsel__detect_missing_brstack_features()` and
  `evsel__detect_missing_aux_action_feature()`; per PMU it is
  `pmu->missing_features.checked`.
- Every call, even after `detection_done`: the helper calls and the tests
  under `check:` run, so the return value is per evsel.
- `exclude_guest`: kept in `pmu->missing_features.exclude_guest`; the
  `exclude_guest` member of `struct perf_missing_features` is neither read nor
  written.
- `struct perf_missing_features` has no `build_id` member.
- Where a new probe goes, directly under the comment "Please add new feature
  detection here." of the matching list:

| Feature | Function | Probe event |
|---|---|---|
| kernel-wide attr bit or flag | `evsel__detect_missing_features()` | scratch software event |
| `branch_sample_type` bit | `evsel__detect_missing_brstack_features()` | the evsel's `type` and `config` |
| depends on the PMU | `evsel__detect_missing_pmu_features()` | the evsel's `type` and `config` |

- A feature perf can drop needs all four:
  - a `bool` in `struct perf_missing_features`
  - the probe, which on failure sets the flag and then resets its bits in the
    scratch attr, so the next probe tests one feature
  - the clear in `evsel__disable_missing_features()`
  - a test under `check:` that returns true when this evsel uses the feature
- Without the `check:` test the function returns false and the open fails
  with `-EINVAL` although the flag is set.
- A feature perf cannot drop gets the `bool` and the probe, no clear and no
  `check:` test, and a message under `EINVAL` in `evsel__open_strerror()`; for
  example `code_page_size` and `data_page_size`.
- `write_backward` and `aux_output`: also rejected with `-EINVAL` by
  `__evsel__prepare_open()` once the flag is set.
