- `its_alloc_pages_node()`: ORs the file-static `gfp_flags_quirk` into every
  request; `its_enable_dma32()` sets it to `GFP_DMA32` on the machines in
  `dma_32bit_impaired_platforms`.
- 32-bit limit: there is no retry and no check of the resulting address.
- `its_alloc_pages_node()`: after allocating, calls `set_memory_decrypted()`
  on `1 << order` pages; `its_free_pages()` calls `set_memory_encrypted()`
  before `free_pages()`.
- `its_free_pages()`: takes the kernel virtual address and the order, not the
  `struct page` that `its_alloc_pages_node()` and `its_alloc_pages()` return.
- Zeroing: `its_alloc_pages_node()` and `its_alloc_pages()` add no
  `__GFP_ZERO`; `itt_alloc_pool()` passes it itself.
- Cache maintenance: none of the helpers calls `gic_flush_dcache_to_poc()`;
  it is left to the caller, for example `its_create_device()` for the ITT.
- `itt_alloc_pool()`: does not round a size below `PAGE_SIZE`;
  `its_create_device()` raises `sz` to at least `ITS_ITT_ALIGN` first.
- `itt_alloc_pool()` with `size >= PAGE_SIZE`: bypasses `itt_pool` and calls
  `its_alloc_pages_node()` with `get_order(size)`.
- `itt_free_pool()`: picks the path by the same size test, so it needs the
  size given at allocation.
- `itt_pool` granule: `its_init()` passes `get_order(ITS_ITT_ALIGN)` to
  `gen_pool_create()`; that is 0, so the pool works in bytes and does not
  align chunks to `ITS_ITT_ALIGN` itself.
- Reused pool chunk: `__GFP_ZERO` applies only when a page is added to
  `itt_pool`; nothing clears a chunk that `gen_pool_free()` returned and
  `gen_pool_alloc()` hands out again.
- Pages are not returned to the allocator, for example:
  - `set_memory_decrypted()` fails: `its_alloc_pages_node()` returns `NULL`
    and leaks the pages.
  - `set_memory_encrypted()` fails: `its_free_pages()` returns without
    `free_pages()`.
  - a page added to `itt_pool`: stays there; the file never removes pool
    memory.
