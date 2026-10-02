- Names table: `__dump_folio()` in `mm/debug.c` has
  `BUILD_BUG_ON(ARRAY_SIZE(pageflag_names) != __NR_PAGEFLAGS + 1)`, so a
  non-alias enum entry without an entry in `__def_pageflag_names` fails the
  build.
- Name wrapper for a config-confined flag, such as `IF_HAVE_PG_MLOCK()` in
  `include/trace/events/mmflags.h`: its `#if` must be the same condition as
  the one around the enum entry, or the build fails in one of the
  configurations.
- Aliases declared after `__NR_PAGEFLAGS`, such as
  `PG_readahead = PG_reclaim`: get no name entry.
- Bit-count build check: the `#error "Not enough bits in page flags"` in
  `include/linux/page-flags-layout.h`; it counts `LRU_GEN_WIDTH` but not
  `LRU_REFS_WIDTH`.
- `LRU_REFS_WIDTH`: `min()` of `__LRU_REFS_WIDTH` and the bits left over, so a
  new flag can shrink it with no build error.
- Node field: with `CONFIG_SPARSEMEM_VMEMMAP` a node that does not fit is
  `#error "Vmemmap: No space for nodes field in page flags"`; it is dropped
  to `NODE_NOT_IN_PAGE_FLAGS` only otherwise.
- `arch/sparc/mm/init_64.c`: has `BUILD_BUG_ON(NR_PAGEFLAGS > 32)`.
- Position: `folio_unlock()` and `folio_end_read()` in `mm/filemap.c` have
  `BUILD_BUG_ON(PG_waiters != 7)`, `BUILD_BUG_ON(PG_locked > 7)` and
  `BUILD_BUG_ON(PG_uptodate > 7)`, so a new entry cannot go among the first
  eight.
- `mminit_verify_pageflags_layout()` in `mm/mm_init.c`: a boot-time check,
  built only with `CONFIG_DEBUG_MEMORY_INIT`; it prints the widths and
  `BUG_ON()`s only on the section, node and zone fields.
- `PAGE_FLAGS_CHECK_AT_PREP`: is `PAGEFLAGS_MASK` without `__PG_HWPOISON`
  (plus the MGLRU masks), so there is nothing to add; every new flag must be
  clear at allocation and `__free_pages_prepare()` wipes it at free.
- A flag that must survive free and allocation: needs the same exemption as
  `__PG_HWPOISON`.
- `PAGE_FLAGS_CHECK_AT_FREE`: an explicit list; add the flag only if finding
  it set at free is a bug.
- Split and migration: `__split_folio_to_order()` in `mm/huge_memory.c`
  copies an explicit list of head flags to each new folio, and
  `folio_migrate_flags()` in `mm/migrate.c` copies flag by flag; a new flag is
  dropped by both unless added.
- Config-confined examples in this tree: `PG_mlocked`, `PG_hwpoison`,
  `PG_young` with `PG_idle`, `PG_arch_2`, `PG_arch_3`; there is no
  PG_uncached.
