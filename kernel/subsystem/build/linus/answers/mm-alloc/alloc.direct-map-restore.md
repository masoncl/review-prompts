- The page allocator does not restore a direct-map entry.
  `debug_pagealloc_map_pages()` in `post_alloc_hook()` maps only when
  debug_pagealloc is enabled.
- No TLB flush follows the restore: neither `secretmem_free_folio()` nor the
  `secretmem_fault()` error path calls `flush_tlb_kernel_range()` after
  `set_direct_map_default_noflush()`.
- `secretmem_free_folio()` ignores the return value of
  `set_direct_map_default_noflush()`.
- `set_direct_map_valid_noflush()`: a third form, taking a page count and a
  bool; `execmem_set_direct_map_valid()` in `mm/execmem.c` uses it.
- Without `CONFIG_ARCH_HAS_SET_DIRECT_MAP`: all three are stubs in
  `include/linux/set_memory.h` that return 0.
- **Unsafe usage**: dropping the last reference to a page whose direct-map
  entry is still invalid.
  - Unsafe: `__free_pages_prepare()` can write the page through the direct
    map: `kernel_poison_pages()` when page poisoning is enabled,
    `clear_highpages_kasan_tagged()` when init-on-free is enabled.
  - Safe: restore in `.free_folio`; `filemap_free_folio()` in `mm/filemap.c`
    calls it before `folio_put_refs()`.
  - Safe: restore, then `folio_put()`, as the `filemap_add_folio()` failure
    path of `secretmem_fault()` does.
  - Safe: `folio_put()` with no restore when
    `set_direct_map_invalid_noflush()` itself returned an error, as
    `secretmem_fault()` does.
  - Safe: `execmem_cache_clean()` calls `execmem_set_direct_map_valid()` with
    true before `vfree()`.
