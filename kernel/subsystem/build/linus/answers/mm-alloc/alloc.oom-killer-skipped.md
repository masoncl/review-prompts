- Skipped with `*did_some_progress = 0`, tested in this order after the
  `ALLOC_WMARK_HIGH` attempt: `PF_DUMPCORE`; order above
  `PAGE_ALLOC_COSTLY_ORDER`; `__GFP_RETRY_MAYFAIL` or `__GFP_THISNODE`;
  `ac->highest_zoneidx < ZONE_NORMAL`; `pm_suspended_storage()`.
- No `__GFP_FS`: `__alloc_pages_may_oom()` has no `__GFP_FS` test; it calls
  `out_of_memory()` in `mm/oom_kill.c`, which returns true without killing
  for a non-memcg request, so progress is 1 and the request loops.
- `__GFP_NOFAIL` in a skipped case: the skip tests jump to `out` before the
  `WARN_ON_ONCE_GFP()` branch, so the request gets progress 0 and no
  `ALLOC_NO_WATERMARKS` attempt; it loops through `nopage` with
  `ALLOC_MIN_RESERVE` only.
- Next step in `__alloc_pages_slowpath()`, in order:
  1. A page was returned: `got_pg`.
  2. `tsk_is_oom_victim(current)` with `ALLOC_OOM` in `alloc_flags` or
     `__GFP_NOMEMALLOC` in the mask: `goto nopage`, even with progress 1.
  3. Progress 1: `no_progress_loops = 0`, `goto retry`.
  4. Progress 0: falls into `nopage`.
