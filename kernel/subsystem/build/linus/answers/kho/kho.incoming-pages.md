- Deferred init: supported; `CONFIG_KEXEC_HANDOVER` has no dependency on
  `CONFIG_DEFERRED_STRUCT_PAGE_INIT` in `kernel/liveupdate/Kconfig`.
- `kho_get_preserved_page()`: under `CONFIG_DEFERRED_STRUCT_PAGE_INIT` it calls
  `init_deferred_page()` for every page of the block before
  `kho_preserved_memory_reserve()` writes `page->private`.
- `memblock_reserved_mark_noinit()`: sets `MEMBLOCK_RSRV_NOINIT`, so
  `memmap_init_reserved_pages()` skips the block and the write survives.
- Deferred pass: `deferred_init_memmap_chunk()` walks
  `for_each_free_mem_range()`, which leaves reserved ranges out.
- Page flags: preserved pages are not marked reserved; the skipped
  `memmap_init_reserved_range()` is what calls `__SetPageReserved()`.
- `kho_init_pages()` and `kho_init_folio()`: run at restore, not at reserve
  time.
- Before the reserve: `kho_populate()` calls
  `memblock_set_kho_scratch_only()`; `memblock_free_all()` clears it.
- `kho_extend_scratch()`: called from `kho_memory_init_early()`; marks as
  scratch every `KHO_SCRATCH_EXT_BLKSIZE` block that holds no preserved memory
  and no node of the incoming radix tree.
- Comment in `kho_restore_page()`: names deserialize_bitmap(), which is not
  defined in this tree; `kho_preserved_memory_reserve()` writes the magic.
