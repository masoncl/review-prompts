- Three call sites, each `check_retry_cpuset() || check_retry_zonelist()`
  followed by `goto restart`:
  1. after the `__GFP_NORETRY` and costly-order exits, before
     `should_reclaim_retry()`;
  2. after the `defrag_mode` retry, before `__alloc_pages_may_oom()`;
  3. at the `nopage` label, before the `nofail` branch and `warn_alloc()`.

| Backward jump to `retry` | Sites passed before the jump |
|---|---|
| after dropping `ac->nodemask` or gaining reserves | none |
| without direct reclaim, under `defrag_mode` | none |
| after the `compact_first` pass | none |
| from `should_reclaim_retry()` | 1 |
| from `should_compact_retry()` | 1 |
| under `defrag_mode` after both declined | 1 |
| after `__alloc_pages_may_oom()` progress | 1 and 2 |
| for `__GFP_NOFAIL` | 3 |

- `goto fail` for `__GFP_NOFAIL` without direct reclaim: comes after site 3,
  so it too can restart instead of failing.
- **Potentially unsafe usage**: a `goto retry` placed above site 1.
  - Unsafe: when the jump can be taken more than once per `restart`; the loop
    then repeats without ever comparing the cpuset or zonelist cookie.
  - Safe: when a flag cleared before the jump limits it to one use, as
    `can_retry_reserves`, `compact_first` and the clearing of
    `ALLOC_NOFRAGMENT` do in `__alloc_pages_slowpath()`; the comment at
    site 1 states the requirement.
