- Fast path: in `__alloc_frozen_pages_noprof()` in `mm/page_alloc.c`;
  `__alloc_pages_noprof()` only wraps it and sets the refcount.
- Slow path flags: there is no gfp_to_alloc_flags() and no ALLOC_HARDER here;
  `alloc_flags_slowpath()` starts from `ALLOC_WMARK_MIN | ALLOC_CPUSET` and
  the result is ORed with `ac->alloc_flags`.
- Early compaction: there is no compaction block before the `retry` label;
  `compact_first`, while set, makes a pass of the loop skip
  `__alloc_pages_direct_reclaim()`.
- One pass from `retry`, in order:
  1. `wake_all_kswapds()` if `ALLOC_KSWAPD`.
  2. `get_page_from_freelist()` with the current `alloc_flags`.
  3. `__gfp_pfmemalloc_flags()`; with reserve flags, or without
     `ALLOC_CPUSET`, `ac->nodemask` is dropped and the first such pass jumps
     back to `retry`, so steps 1 and 2 repeat with the new flags and no
     nodemask.
  4. `goto nopage` without `__GFP_DIRECT_RECLAIM` (under `defrag_mode`, after
     one retry without `ALLOC_NOFRAGMENT`) or under `PF_MEMALLOC`.
  5. `__alloc_pages_direct_reclaim()`, unless `compact_first`.
  6. `__alloc_pages_direct_compact()` at `compact_priority`.
  7. With `compact_first`: clear it and `goto retry`, so the next pass does
     reclaim, then compaction.
  8. `__GFP_NORETRY` and costly-order exits, retry decisions,
     `__alloc_pages_may_oom()`.
- Reserves versus first compaction: the reserves attempt (step 3) comes before
  the first compaction, and a `PF_MEMALLOC` task or a request without direct
  reclaim never compacts.
- `compact_first` condition: `can_compact` and (`costly_order`, or
  `order > 0` with `ac->migratetype != MIGRATE_MOVABLE`); it does not call
  `gfp_pfmemalloc_allowed()`, so an OOM victim or `__GFP_MEMALLOC` request
  can compact first.
- `compact_first` pass failed, `__GFP_NORETRY` and `__GFP_THISNODE` both set:
  `goto nopage` with no direct reclaim, at any order; the code does not test
  `COMPACT_SKIPPED` or `COMPACT_DEFERRED` here.
- `compact_first` pass failed, `__GFP_NORETRY` alone: the next pass keeps
  `INIT_COMPACT_PRIORITY`; without `__GFP_NORETRY` it goes to
  `DEF_COMPACT_PRIORITY`.
