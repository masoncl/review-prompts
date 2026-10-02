- `ALLOC_NOLOCK` request (`alloc_frozen_pages_nolock_noprof()`): NULL after the
  single fast-path attempt; never enters the slow path.
- `order > MAX_PAGE_ORDER`: `alloc_order_allowed()` warns (not with
  `__GFP_NOWARN`) and `__alloc_frozen_pages_noprof()` returns NULL before the
  fast path, also with `__GFP_NOFAIL`.
- Non-costly order, direct reclaim, no modifier: retried without bound while
  `__alloc_pages_may_oom()` reports progress; it still returns NULL in the
  cases listed under "OOM killer exceptions".
- `__GFP_RETRY_MAYFAIL` at a costly order: has an effect in
  `__alloc_pages_slowpath()` only if `can_compact`, which needs
  `__GFP_DIRECT_RECLAIM`, `__GFP_IO` and `CONFIG_COMPACTION` (see
  `gfp_compaction_allowed()` in `include/linux/gfp.h`); otherwise the request
  fails after one pass as if the flag were absent.
- `__GFP_NORETRY` with `__GFP_RETRY_MAYFAIL`: `__GFP_NORETRY` is tested first
  and wins.
- `__GFP_NOFAIL` with `__GFP_NORETRY` or `__GFP_RETRY_MAYFAIL`: with
  `__GFP_DIRECT_RECLAIM` the request still loops without bound, because every
  `goto nopage` ends in the `nofail` branch.
- `__GFP_NOFAIL` and order: `mm/page_alloc.c` has no order test for
  `__GFP_NOFAIL` other than `alloc_order_allowed()`; an order above 1 gets no
  warning, and the "order > 1 is not supported" text in
  `include/linux/gfp_types.h` is not enforced by the page allocator.
- `__GFP_NOFAIL` at a costly order: loops through `nopage` and reaches
  `out_of_memory()` never; without `__GFP_RETRY_MAYFAIL` it exits to `nopage`
  before `__alloc_pages_may_oom()`, with it `__alloc_pages_may_oom()` skips.
- `__GFP_NOFAIL` warnings in `__alloc_pages_slowpath()`: exactly two
  `WARN_ON_ONCE()` at entry, for no `__GFP_DIRECT_RECLAIM` and for
  `PF_MEMALLOC`.
- `__GFP_NOFAIL` with `__GFP_DIRECT_RECLAIM` under `PF_MEMALLOC`: warns once,
  then loops between `retry` and `nopage` with no reclaim, trying only the
  freelist and the `ALLOC_MIN_RESERVE` fallback.
- `__GFP_NOFAIL` in `__alloc_pages_may_oom()`: gets the `ALLOC_NO_WATERMARKS`
  attempt on every call that reaches `out_of_memory()`, whatever it returns;
  `WARN_ON_ONCE_GFP()` fires only when `out_of_memory()` returned false.
