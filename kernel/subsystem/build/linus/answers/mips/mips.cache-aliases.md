- `__flush_dcache_pages()` exists only under `arch/arc`; on MIPS
  `__flush_dcache_folio_pages()` in `arch/mips/mm/cache.c` does that, called
  by `flush_dcache_folio()` and `flush_dcache_page()` in
  `arch/mips/include/asm/cacheflush.h`.
- Deferral test: made on the `struct address_space`, not on the folio:
  `folio_flush_mapping()` is non-NULL and `mapping_mapped()` is false.
- A folio of a file that has any user mapping is flushed at once, even if
  this folio is mapped nowhere.
- Anonymous and swap-cache folios: `folio_flush_mapping()` returns NULL, so
  they are flushed at once.
- `__update_cache()`: called from `set_ptes()` in
  `arch/mips/include/asm/pgtable.h`, before the PTE is written;
  `update_mmu_cache_range()` calls only `__update_tlb()`.
- `set_ptes()` skips `__update_cache()` when the new PTE is not present, or
  every slot already holds a present PTE with the pfn of the new PTE.
- `__update_cache()`: flushes through `kmap_local_folio()`, the kernel
  address; it does not call `kmap_coherent()`.
- `__update_cache()`: its only early return is for `!pfn_valid()`; it does
  not test `cpu_has_dc_aliases`.
- `kmap_coherent()`: every caller under `arch/mips` tests `folio_mapped()`
  and `!folio_test_dcache_dirty()` first, for example `copy_to_user_page()`
  and `local_r4k_flush_cache_page()` in `arch/mips/mm/c-r4k.c`.
- `cpu_has_dc_aliases` for `kmap_coherent()`: tested in the same expression
  by every caller except `__flush_anon_page()`, where the caller
  `flush_anon_page()` tests it and `__flush_anon_page()` tests
  `pages_do_alias()`.
- `__flush_dcache_folio_pages()` does not call `kmap_coherent()`; it flushes
  the `kmap_local_page()` address.
- Clearing a user page: `clear_user_page()` in
  `arch/mips/include/asm/page.h` writes through the kernel address and
  flushes when `pages_do_alias()`; it does not call `kmap_coherent()`.
- `copy_user_highpage()`: `kmap_coherent()` maps the source only; the
  destination is written through `kmap_atomic()` and flushed when
  `!cpu_has_ic_fills_f_dc` or `pages_do_alias()`.
- `__kmap_pgprot()` checks only the dirty flag; `folio_mapped()` is tested by
  the callers, not inside it.
- **Unsafe usage**: calling `kmap_coherent()` on a folio whose
  `PG_dcache_dirty` is set; the `BUG_ON()` at the top of `__kmap_pgprot()`
  fires.
  - Safe: test `!folio_test_dcache_dirty()` first and fall back to the kernel
    address, as `copy_to_user_page()` does.
