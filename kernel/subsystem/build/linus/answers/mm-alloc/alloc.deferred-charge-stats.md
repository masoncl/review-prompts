- `kmem_cache_charge()`: calls `memcg_slab_post_charge()`, which calls
  `__memcg_slab_post_alloc_hook()` directly; neither `__GFP_ACCOUNT` nor
  `SLAB_ACCOUNT` is tested, and there is no virt_to_cache() here.
- Skipped cache: `memcg_slab_post_charge()` returns true without charging when
  `!cache_needs_objcg(s)`, that is, the cache lacks `SLAB_MAY_ACCOUNT`.
- Returns true with no charge and no statistics change also when the objcg is
  the root objcg, and when `alloc_slab_obj_exts()` fails.
- Slab object, memcg side: `__account_obj_stock()` adds `obj_full_size()` to
  the memcg's `cache_vmstat_idx()` counter; there is no mod_objcg_state()
  here.
- Slab object, node side: not touched by the late charge or by the per-object
  free; only `account_slab()` and `unaccount_slab()` change it.
- Large kmalloc is handled first, tested with `PageLargeKmalloc()`:
  - already charged (`PageMemcgKmem()`): returns true;
  - charges with `__memcg_kmem_charge_page()`;
  - then `mod_node_page_state()` subtracts the size from
    `NR_SLAB_UNRECLAIMABLE_B` and `mod_lruvec_page_state()` adds it back, so
    the node is net zero and the memcg gains the size.
- Large kmalloc under a root objcg: `__memcg_kmem_charge_page()` returns 0
  without setting `memcg_data`; both updates hit the node only, net zero.
- Large kmalloc free: `free_large_kmalloc()` subtracts with
  `mod_lruvec_page_state()` before the page is uncharged in
  `__free_pages_prepare()`, so for a charged page node and memcg are both
  decremented.
- Caller in this tree: `__sk_charge()` in `net/core/sock.c`, which adds
  `__GFP_NOFAIL`.
