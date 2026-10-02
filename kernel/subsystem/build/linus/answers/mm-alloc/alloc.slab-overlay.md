- `page_slab()` in `mm/slab.h`: takes `compound_head()` first, then tests
  `page_type >> 24` against `PGTY_slab`. It returns NULL for anything else,
  large kmalloc pages (`PGTY_large_kmalloc`) included.
- Page type: set with `__SetPageSlab()` in `alloc_slab_page()`, on the head
  page only, and cleared with `__ClearPageSlab()` in `__free_slab()`.
  `mm/slub.c` does not call `__folio_set_slab()` or `folio_test_slab()`.
- `PageSlab()` on a tail page of a slab: false. Code that holds an arbitrary
  address uses `virt_to_slab()`.
- `enum slab_flags` in `mm/slub.c`: names the bits of `slab->flags` that slab
  code uses; it plays no part in identifying a slab.
- `SLAB_MATCH()`: `slab_cache` is matched against `compound_info`, the word
  after `flags` in `struct page`; `struct page` has no field named
  `compound_head`. No `SLAB_MATCH()` line covers `__page_type`.
- Without `CONFIG_MEMCG` and with `CONFIG_SLAB_OBJ_EXT`: `obj_exts` is matched
  against `_unused_slab_obj_exts`.
- A new field must leave alone: bit 0 of the `compound_info` word, the
  `page_type` word, `_refcount`, and `memcg_data`.
- `page->mapping`: overlaid by `slab_list.prev` and by the function pointer
  of `rcu_head`. `__free_slab()` sets `page->mapping = NULL` because
  `page_expected_state()` in `mm/page_alloc.c` rejects anything else.
- `SL_pfmemalloc` is `PG_active`, which is in `PAGE_FLAGS_CHECK_AT_FREE`;
  `__free_slab()` clears it with `__slab_clear_pfmemalloc()`.
- pfmemalloc mark: `page_is_pfmemalloc()` reads `page->lru.next`, the word
  that becomes `slab->slab_cache`. `alloc_slab_page()` copies it to
  `SL_pfmemalloc` before `allocate_slab()` writes `slab_cache`.
- `allocate_slab()` sets: `counters = 0`, `objects`, `obj_exts_needs_objcg`
  (64-bit), `slab_cache`, and `obj_exts` through `init_slab_obj_exts()`,
  `alloc_slab_obj_exts_early()` and `account_slab()`.
- `slab->counters = 0`: the only place where `frozen`, `inuse` and the
  64-bit bits `obj_exts_in_object` and `obj_exts_needs_objcg` of a new slab
  are cleared.
- `allocate_slab()` does not write `freelist`, run constructors, add the slab
  to a list or call `inc_slabs_node()`. There is no shuffle_freelist().
- Freelist of a new slab: built by the caller with `init_slab_obj_iter()`,
  `next_slab_obj()` and `build_slab_freelist()`, as `alloc_from_new_slab()`
  does. The caller hands out the objects it wants first, sets `inuse`, and
  links only the rest.
- `frozen`: set only by `alloc_debug_processing()`, to retire a slab that
  failed a consistency check.
