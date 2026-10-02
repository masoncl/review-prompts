- `gfpflags_allow_spinning()`: returns `gfp & __GFP_RECLAIM`, true if either
  reclaim bit is set.
- `mm/page_alloc.c` and `mm/slub.c` do not call it: trylock-only mode comes
  from `ALLOC_NOLOCK` in `mm/page_alloc.h` and `SLAB_ALLOC_NOLOCK` in
  `mm/slab.h`, set for `alloc_pages_nolock()` and `kmalloc_nolock()`
  requests.
- A mask with no reclaim bit passed to `alloc_pages()` or `kmalloc()`: still
  spins on locks, for example `zone->lock` in `rmqueue_buddy()`.
- `gfpflags_allow_spinning()` is tested outside the allocators, for example
  in `try_charge_memcg()` and `stack_depot_save_flags()`;
  `__reset_page_owner()` passes `__GFP_NOWARN` alone to make it false.
- `gfp_has_flags()` in `include/linux/gfp.h`: the helper for
  `(gfp & flags) == flags`; `gfp_has_io_fs()` is built on it.
- `__kvmalloc_node_noprof()`: has no test against `GFP_KERNEL`.
- In-tree subset tests against `GFP_KERNEL`, for example:
  - `nfs_release_folio()` in `fs/nfs/file.c`:
    `(current_gfp_context(gfp) & GFP_KERNEL) != GFP_KERNEL`, scope applied
    first.
  - `rpcauth_cache_shrink_scan()` in `net/sunrpc/auth.c`:
    `(sc->gfp_mask & GFP_KERNEL) != GFP_KERNEL`.
- `objpool_init_percpu_slots()` in `lib/objpool.c`: masks with
  `GFP_ATOMIC | GFP_KERNEL` and compares with `GFP_ATOMIC`, which also
  requires `__GFP_DIRECT_RECLAIM`, `__GFP_IO` and `__GFP_FS` to be clear.
- **Potentially unsafe usage**: `(gfp & GFP_ATOMIC) == GFP_ATOMIC` or
  `(gfp & GFP_NOWAIT) == GFP_NOWAIT` as a test for "cannot sleep"; the first
  is true for `GFP_KERNEL | __GFP_HIGH`, the second for
  `GFP_KERNEL | __GFP_NOWARN`.
  - Unsafe: when the result decides whether the code may sleep; the first
    test is also false for `GFP_NOWAIT`, the second for `GFP_ATOMIC`, and
    neither constant holds `__GFP_DIRECT_RECLAIM`, the bit that
    `gfpflags_allow_blocking()` tests.
  - Safe: `!gfpflags_allow_blocking(gfp)`, as `pcpu_alloc_noprof()` uses.
  - Safe: when neither result leads to a sleep that the mask does not
    allow: `ib_nl_make_request()` in `drivers/infiniband/core/sa_query.c`
    picks `GFP_ATOMIC` or `GFP_NOWAIT`, and
    `__page_pool_alloc_netmems_slow()` in `net/core/page_pool.c` only adds
    `__GFP_NOWARN`.
- **Potentially unsafe usage**: `gfp == GFP_KERNEL`.
  - Unsafe: when callers may add modifier bits and a false result picks the
    path that must not be taken.
  - Safe: when a false result only skips an optional step, as in
    `bpf_mem_cache_alloc_flags()`, which skips its `__alloc()` fallback.
