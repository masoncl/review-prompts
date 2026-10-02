- The flags are in `mm/page_alloc.h`. The trylock flag is `ALLOC_NOLOCK`; there
  is no ALLOC_TRYLOCK.
- There is no gfp_to_alloc_flags() or gfp_to_alloc_flags_cma() here.
  `alloc_flags_slowpath()`, `alloc_flags_nonblocking()` and `alloc_flags_cma()`
  in `mm/page_alloc.c` do those jobs.
- Entry point for caller flags: the fifth argument of
  `__alloc_frozen_pages_noprof()` and `__alloc_pages_noprof()`.
- Accepted there: only `ALLOC_NOLOCK` and `ALLOC_NO_CODETAG`. Any other bit:
  `WARN_ON()` and `NULL`.
- `ALLOC_DEFAULT`: 0; what every other caller passes.
- Caller flags are kept in `alloc_flags` of `struct alloc_context` and OR-ed
  into every slow-path recomputation, so they last the whole allocation.
- `ALLOC_NOLOCK`: passed only by `alloc_frozen_pages_nolock_noprof()`. Code
  outside mm/ selects it with `alloc_pages_nolock()`.
- `ALLOC_NO_CODETAG`: passed only by `__alloc_tag_add_early_pfn()` in
  `mm/alloc_tag.c`, which calls `clear_page_tag_ref()` before `__free_page()`.
  `alloc_tag_add_early_pfn()` tests it.

| Flag | Differs from the usual belief |
|---|---|
| `ALLOC_WMARK_LOW` | fast path only without `ALLOC_NOLOCK`; with it the fast path uses `ALLOC_WMARK_MIN` |
| `ALLOC_HIGHATOMIC` | needs `__GFP_HIGH`, order > 0, no `__GFP_DIRECT_RECLAIM`, no `__GFP_NOMEMALLOC`; set on the fast path too |
| `ALLOC_MIN_RESERVE` | `__GFP_HIGH`; or `rt_or_dl_task()` and `in_task()` when the request has `__GFP_DIRECT_RECLAIM`; or the `__GFP_NOFAIL` attempt at the `nopage` label |
| `ALLOC_NON_BLOCK` | not implied by `ALLOC_MIN_RESERVE`; only from `alloc_flags_nonblocking()` |
| `ALLOC_NOFRAGMENT` | also set whenever `defrag_mode` is on, by `alloc_flags_nofragment()` and `alloc_flags_slowpath()` |
| `ALLOC_KSWAPD` | fast path gets it from `alloc_flags_nofragment()`, so never with `ALLOC_NOLOCK` |
| `ALLOC_CPUSET` | forced on in `__alloc_pages_may_oom()` and the first try of `__alloc_pages_cpuset_fallback()` |

- `get_page_from_freelist()`: drops `ALLOC_NOFRAGMENT` and retries only when
  `defrag_mode` is off. With `defrag_mode`, `__alloc_pages_slowpath()` drops it.
- `__GFP_HIGH` and `__GFP_KSWAPD_RECLAIM`: tested explicitly; nothing asserts
  that their values equal `ALLOC_MIN_RESERVE` and `ALLOC_KSWAPD`.
- With `ALLOC_NOLOCK`, `__alloc_frozen_pages_noprof()` also: requires
  `pcp_allowed_order()`, returns `NULL` when `alloc_nolock_allowed()` is false,
  ORs in `gfp_nolock`, and has a `VM_WARN_ON_ONCE()` for any gfp bit other
  than `__GFP_ACCOUNT` and the `gfp_nolock` bits.
