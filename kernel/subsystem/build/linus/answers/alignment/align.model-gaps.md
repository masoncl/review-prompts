- Models take a large `kmalloc()` to be an ordinary refcounted compound
  page. `free_large_kmalloc()` in `mm/slub.c` frees it with
  `free_frozen_pages()`.
- Models know the `CMA_MIN_ALIGNMENT_BYTES` rule only for
  `cma_init_reserved_mem()` and `cma_declare_contiguous_nid()`.
  `cma_declare_contiguous_multi()` aligns the start and end of each
  candidate range to at least it, and `cma_reserve_early()` returns `NULL`
  for a size that is not aligned to it.
- Models take the tools `PAGE_MASK` to match the kernel one.
  `tools/include/linux/mm.h` fixes `PAGE_SHIFT` at 12 and defines
  `PAGE_MASK` as `unsigned long` in every build.
