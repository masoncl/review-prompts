- `alloc_frozen_pages_nolock_noprof()`: only maps `NUMA_NO_NODE` to
  `numa_node_id()` and calls the shared `__alloc_frozen_pages_noprof()` with
  `ALLOC_NOLOCK`; the nolock branches live in it and its callees.
- `gfp_nolock`: a `static const gfp_t` in `mm/page_alloc.c`, equal to
  `__GFP_NOWARN | __GFP_ZERO | __GFP_NOMEMALLOC | __GFP_COMP`; it is ORed
  into the caller's gfp.
- Accepted without a warning: `__GFP_ACCOUNT` and the four `gfp_nolock`
  bits.
- Any other caller bit: only trips `VM_WARN_ON_ONCE()`; the `ALLOC_NOLOCK`
  branch does not clear it and the allocation proceeds.
- Orders: `alloc_order_allowed()` returns `pcp_allowed_order(order)` for
  `ALLOC_NOLOCK`; any other order returns NULL with no warning.
- Order of the early tests: order first, then the gfp warning, then
  `alloc_nolock_allowed()`.
- `alloc_nolock_allowed()` fails when `can_spin_trylock()` in `mm/internal.h`
  is false or `deferred_pages_enabled()` is true.
- `can_spin_trylock()` is false in two cases: `CONFIG_PREEMPT_RT` in NMI or
  hardirq, and `!CONFIG_SMP` in NMI.
- `__alloc_frozen_pages_noprof()` makes no test of an arch primitive such as
  cmpxchg support.
- memcg charge failure: the page is freed with
  `__free_frozen_pages(page, order, FPI_NOLOCK)`, not `free_pages_nolock()`.
