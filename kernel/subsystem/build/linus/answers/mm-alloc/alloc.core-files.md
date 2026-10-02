| Job | File | Easy to miss |
|---|---|---|
| GFP bit definitions | `include/linux/gfp_types.h` | Also holds the composites such as `GFP_KERNEL` and `GFP_ATOMIC`; `include/linux/gfp.h` defines none of them. mm-only masks `GFP_BOOT_MASK`, `GFP_RECLAIM_MASK`, `GFP_SLAB_BUG_MASK` are in `mm/internal.h`. |
| Helpers that test a mask | `include/linux/gfp.h` | `gfp_migratetype()` is not here; it is in `mm/page_alloc.h`. There is no gfpflags_normal_context() in this tree. |
| Page allocator, mm-internal declarations | `mm/page_alloc.h` | Holds the `ALLOC_` flags (`ALLOC_NOLOCK`, `ALLOC_NO_CODETAG`), `struct alloc_context`, `__alloc_frozen_pages_noprof()`, `free_frozen_pages()` and also `__alloc_pages_noprof()`. `mm/internal.h` holds none of these and does not include `mm/page_alloc.h`; a file that uses both includes both, as `mm/slub.c` does. |
| What stays in `mm/internal.h` | `mm/internal.h` | `set_page_refcounted()`, `can_spin_trylock()`, `struct compact_control`, `struct capture_control`. |
| Slab internal header | `mm/slab.h` | Also holds slab's own flags (`SLAB_ALLOC_NOLOCK` and the other `SLAB_ALLOC_` and `SLAB_FREE_` values) and the inline `kmalloc_slab()`. `struct slab_alloc_context` is in `mm/slub.c`; it is a separate type from `struct alloc_context`. |
| Code shared by all kmalloc caches | `mm/slab_common.c` | Holds `kmalloc_caches[]`, `kmalloc_info[]`, `kmalloc_size_index[]`. `kmalloc_slab()` is in `mm/slab.h`; `__kmalloc_large_noprof()` is in `mm/slub.c`. |
| vmalloc | `mm/vmalloc.c` | mm-internal declarations are in `mm/vmalloc.h`. |
| Boot allocator hand-over | `mm/memblock.c`, `mm/mm_init.h` | `memblock_free_all()` is declared only in `mm/mm_init.h`; `memblock_free_pages()` is defined in `mm/mm_init.c`. |
| Allocation profiling | `mm/alloc_tag.c`, `include/linux/alloc_tag.h` | There is no alloc_tag.c under `lib/`; only `lib/codetag.c` is there. Page hooks `pgalloc_tag_add()` and `pgalloc_tag_sub()` are static in `mm/page_alloc.c`; slab hook `alloc_tagging_slab_alloc_hook()` is in `mm/slub.c`; `include/linux/pgalloc_tag.h` holds the page tag reference accessors, not these hooks. |
| Page allocator, slab allocator, mempools, zone and watermark initialisation, memory policy | — | Models have this right; see `mm/page_alloc.c`, `mm/slub.c`, `mm/mempool.c`, `mm/mm_init.c` (zones; the watermarks are set in `mm/page_alloc.c`), `mm/mempolicy.c`. |
