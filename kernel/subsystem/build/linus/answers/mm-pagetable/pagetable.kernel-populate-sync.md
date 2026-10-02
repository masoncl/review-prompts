- `include/linux/pgalloc.h`: defines only `pgd_populate_kernel()` and
  `p4d_populate_kernel()`; both are macros that take `addr` first and always
  act on `init_mm`.
- PMD-level masks: x86-32 sets `ARCH_PAGE_TABLE_SYNC_MASK` to
  `PGTBL_PMD_MODIFIED`, and so does arm with `CONFIG_VMAP_STACK` and without
  `CONFIG_ARM_LPAE`; the two macros test only `PGTBL_PGD_MODIFIED` and
  `PGTBL_P4D_MODIFIED`, so they never sync there.
- PUD and PMD levels: there is no populate helper that syncs; a caller tracks
  a mask and calls `arch_sync_kernel_mappings()` itself, as
  `__apply_to_page_range()` does.
- `pgtbl_mod_mask`: a typedef of `unsigned int`, not an enum; the bits are
  macros in `include/linux/pgtable.h`.
- Track helpers: in `mm/pgalloc-track.h`, included only by `mm/memory.c` and
  `mm/vmalloc.c`.
- Bit set by a track helper: the level of the entry written, one above the
  table allocated; `p4d_alloc_track()` sets `PGTBL_PGD_MODIFIED`,
  `pte_alloc_kernel_track()` sets `PGTBL_PMD_MODIFIED`.
- `end` on x86-64: `sync_global_pgds()` in `arch/x86/mm/init_64.c` treats it
  as inclusive, which is why the macros pass `(addr, addr)`; the two callers
  in that file that have an exclusive end pass `end - 1`.
- arm `arch_sync_kernel_mappings()` in `arch/arm/kernel/traps.c`: copies
  nothing; it bumps `init_mm.context.vmalloc_seq`, and only for a range that
  overlaps vmalloc space.
- **Potentially unsafe usage**: `pgd_populate()` or `p4d_populate()` on
  `init_mm` with no sync after it.
  - Unsafe: at run time, on an arch whose `ARCH_PAGE_TABLE_SYNC_MASK` covers
    that level; page tables already on `pgd_list` never get the entry.
  - Safe: where the mask is the default 0 from `include/linux/pgtable.h`, as
    in `modify_pagetable()` in `arch/s390/mm/vmem.c`.
  - Safe: in `__init` code that runs before any other pgd is allocated, such
    as `kasan_populate_pgd()` in `arch/x86/mm/kasan_init_64.c`; `pgd_ctor()`
    in `arch/x86/mm/pgtable.c` copies the kernel entries of `swapper_pg_dir`
    into each later pgd.
  - Safe: when the arch sync is called directly afterwards, as
    `__kernel_physical_mapping_init()` calls `sync_global_pgds()`.
