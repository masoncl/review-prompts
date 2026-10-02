- `__init_memblock` and `__initdata_memblock` in
  `include/linux/memblock.h`: `__meminit` and `__meminitdata` without
  `CONFIG_ARCH_KEEP_MEMBLOCK`, empty with it.
- `__meminit` in `include/linux/init.h` is empty under
  `CONFIG_MEMORY_HOTPLUG`, so code marked `__init_memblock` and the static
  arrays are discarded only when both `CONFIG_ARCH_KEEP_MEMBLOCK` and
  `CONFIG_MEMORY_HOTPLUG` are off.
- `memblock_discard()` (without `CONFIG_ARCH_KEEP_MEMBLOCK`): frees resized
  arrays but leaves `memblock.memory.regions` and
  `memblock.reserved.regions` pointing at them, and sets `memblock_memory`
  to NULL; the data is stale afterwards even when `CONFIG_MEMORY_HOTPLUG`
  keeps the section.
- `physmem` and `memblock_physmem_init_regions` in `mm/memblock.c` carry no
  `__initdata_memblock`; they survive in every configuration that has
  `CONFIG_HAVE_MEMBLOCK_PHYS_MAP`.
- Allocation failure: `memblock_alloc_try_nid()` and
  `memblock_alloc_range_nid()` only return NULL or 0; the only message
  `memblock_alloc_range_nid()` itself prints on failure is
  `pr_warn_ratelimited()` when mirrored memory runs out and the search is
  retried.
- There is no memblock_free_late() in this tree; `memblock_phys_free()`
  (and `memblock_free()`, which wraps it) does that job.
- `memblock_phys_free()` once `slab_is_available()`: hands the pages to the
  buddy allocator through `__free_reserved_area()`; `memblock_discard()`
  relies on this.
- `memblock.reserved` after a late free: `memblock_phys_free()` and
  `free_reserved_area()` remove the range only with
  `CONFIG_ARCH_KEEP_MEMBLOCK`.
- `memblock_free()` and `memblock_phys_free()` are `__init_memblock`;
  `free_reserved_area()` has no section annotation, so it is usable from
  non-init code in every configuration.
- **Potentially unsafe usage**: `memblock_free()` or `memblock_phys_free()`
  after `memblock_free_all()`.
  - Unsafe: before `slab_is_available()` is true; only `memblock.reserved`
    is edited and the pages never reach the buddy allocator.
  - Unsafe: with `CONFIG_DEFERRED_STRUCT_PAGE_INIT`, before
    `page_alloc_init_late()` disables `deferred_pages`;
    `__free_reserved_area()` WARNs and frees nothing. The same holds for
    `free_reserved_area()`.
  - Safe: after `page_alloc_init_late()` has disabled `deferred_pages`, as
    `memblock_discard()` does.
- **Potentially unsafe usage**: `kfree()` or `free_pages()` on memory
  obtained from memblock.
  - Unsafe: when memblock served the allocation; the pages are
    `PageReserved` and need what `free_reserved_pages()` in
    `mm/page_alloc.c` does (clear reserved, zero the count,
    `adjust_managed_page_count()`).
  - Safe: `kfree()` when the allocation was made after
    `slab_is_available()` and so came from the slab; `memblock_discard()`
    chooses between `kfree()` and `memblock_free()` with
    `memblock_memory_in_slab` and `memblock_reserved_in_slab`, which
    `memblock_double_array()` records.
