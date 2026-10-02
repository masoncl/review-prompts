- Partition names: there is no KMALLOC_RANDOM_START, KMALLOC_RANDOM_END or
  RANDOM_KMALLOC_CACHES_NR here. The normal caches are split under
  `CONFIG_KMALLOC_PARTITION_CACHES` into `KMALLOC_PARTITION_START` to
  `KMALLOC_PARTITION_END` (`KMALLOC_PARTITION_CACHES_NR` + 1 = 16 rows). Row 0
  is `KMALLOC_NORMAL`, named "kmalloc-<size>"; the other 15 are named
  "kmalloc-part-NN-<size>".
- `RANDOM_KMALLOC_CACHES`: only a transitional symbol in `mm/Kconfig` that sets
  the default of `KMALLOC_PARTITION_CACHES`; no C code tests it.
- Partition key: a `kmalloc_token_t`, built by `__kmalloc_token()` where the
  `kmalloc()` macro expands, not `_RET_IP_` inside the allocator.

  | Mode | Token | Row chosen by `kmalloc_type()` |
  |---|---|---|
  | `CONFIG_KMALLOC_PARTITION_RANDOM` | `_CODE_LOCATION_` | `hash_64()` of token XOR `random_kmalloc_seed`, 4 bits |
  | `CONFIG_KMALLOC_PARTITION_TYPED` | `__builtin_infer_alloc_token()` of the call's arguments | the token itself; `Makefile` bounds it with `-falloc-token-max=16` |

- Token plumbing: the token is an extra parameter of the out-of-line
  allocators that pick a cache, for example `__kmalloc_noprof()`, hidden by
  `DECL_TOKEN_PARAMS()` and `PASS_TOKEN_PARAMS()` in `include/linux/slab.h`
  (`DECL_KMALLOC_PARAMS()` and `PASS_KMALLOC_PARAMS()` where a bucket is passed
  too); a new wrapper must pass it on, as `_kmalloc_array_noprof()` does.
- `KMALLOC_NO_OBJ_EXT` (`CONFIG_SLAB_OBJ_EXT`, "kmalloc-no-objext-<size>"): a
  row that no GFP bit selects; `kmalloc_slab()` in `mm/slab.h` forces it when
  `alloc_flags` has `SLAB_ALLOC_NO_OBJ_EXT`, after `kmalloc_type()` ran.
- Large path: there is no __kmalloc_large_node() here; `___kmalloc_large_node()`
  in `mm/slub.c` does the work. It does not call `alloc_pages_node()`; it uses
  `alloc_frozen_pages_noprof()` or `__alloc_frozen_pages_noprof()` and then
  `__SetPageLargeKmalloc()`.
- `kfree()`: does not call `virt_to_folio()`; it uses `virt_to_page()` and
  `page_slab()`, which tests `PGTY_slab` on the compound head. NULL means a
  large allocation.
- `free_large_kmalloc()`: if `PageLargeKmalloc()` is false it warns once,
  calls `dump_page()` and returns without freeing.
