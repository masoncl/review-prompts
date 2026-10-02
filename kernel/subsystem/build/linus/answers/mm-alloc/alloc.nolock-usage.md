- `alloc_nolock_allowed()`: takes no argument and is called once, in
  `__alloc_frozen_pages_noprof()`; it is the entry gate, not what a helper
  calls.
- A helper that receives `alloc_flags` tests `alloc_flags & ALLOC_NOLOCK`
  itself; there is no ALLOC_TRYLOCK.
- A helper that sees only gfp tests `gfpflags_allow_spinning()`; for example
  `stack_depot_save_flags()` in `lib/stackdepot.c` and
  `add_stack_record_to_list()` in `mm/page_owner.c`, both reached from
  `post_alloc_hook()`.
- A reclaim bit passed by the caller is not cleared by the `ALLOC_NOLOCK`
  branch, so those gfp-only tests can then see a request that may spin.
- Helpers that take a lock with no test, for example, and what keeps them
  unreachable:

| Helper | Lock | What excludes it |
|---|---|---|
| `_deferred_grow_zone()` | `pgdat_resize_lock()` | `alloc_nolock_allowed()` fails while `deferred_pages_enabled()` |
| `reserve_highatomic_pageblock()` | `zone->lock` | needs `ALLOC_HIGHATOMIC` |
| `wakeup_kswapd()` in `rmqueue()` | waitqueue | needs `ALLOC_KSWAPD` |
| `cpuset_current_node_allowed()` | `callback_lock` | returns first for `__GFP_HARDWALL` |

- `ALLOC_HIGHATOMIC`: the fast path does compute it, as
  `alloc_flags_nonblocking(gfp, order) & ALLOC_HIGHATOMIC`; it stays clear
  because `alloc_flags_nonblocking()` returns 0 for `__GFP_NOMEMALLOC`, which
  `gfp_nolock` contains.
- gfp_to_alloc_flags() is not in this tree; `alloc_flags_slowpath()` does
  that job and is not reached with `ALLOC_NOLOCK`.
- `ALLOC_KSWAPD`: its only fast-path setter is `alloc_flags_nofragment()`,
  which `__alloc_frozen_pages_noprof()` skips for `ALLOC_NOLOCK`.
- `__GFP_HARDWALL`: `prepare_alloc_pages()` sets it in the gfp handed to
  `get_page_from_freelist()` whenever `cpusets_enabled()`.
