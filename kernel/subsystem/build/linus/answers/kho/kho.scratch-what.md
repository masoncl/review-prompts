- Count: `nodes_weight(node_states[N_MEMORY]) + 2`, not the number of online
  nodes; the per-node loop is `for_each_node_state(nid, N_MEMORY)`, so a
  memoryless node gets no region.
- `kho_reserve_scratch()` runs only when `kho_in.scratch_phys` is 0, that is
  with no handover data or with handover data that was rejected:
  `kho_memory_init()` calls it then, and it returns at once when `kho_enable`
  is false.
- KHO boot: `kho_scratch` and `kho_scratch_cnt` are inherited from the
  previous kernel in `kho_populate()` and `kho_memory_init_early()`; the
  `kho_scratch=` sizes are then not used.
- Alignment and size rounding: `SCRATCH_ALIGNMENT_BYTES`
  (`PAGE_SIZE * MAX_ORDER_NR_PAGES`) in `kernel/liveupdate/kexec_handover.c`,
  not `CMA_MIN_ALIGNMENT_BYTES`; a `static_assert()` only requires it to be at
  least that.
- Default size: `scratch_scale` is 200 (percent), applied to
  `memblock_reserved_kern_size()` minus `memblock_reserved_hugetlb_size()`;
  see `scratch_size_update()` and `scratch_size_node()`.
- Default global size: the scaled total minus the lowmem size, not the scaled
  total.
- `kho_scratch=` explicit form: three comma-separated sizes, in the order
  lowmem, global, per-node; see `kho_parse_scratch_size()`.
- `kho_reserve_scratch()` does not call `memblock_mark_kho_scratch()`; the
  `MEMBLOCK_KHO_SCRATCH` flag is set by `kho_populate()` in the next kernel.
- Migrate type on a cold boot: `kho_init()` calls
  `init_cma_reserved_pageblock()` on every scratch pageblock, which sets
  `MIGRATE_CMA` and frees the pages to the buddy allocator; there is no
  kho_init_scratch_pages() and KHO does not call
  `set_pageblock_migratetype()`.
- `kho_init()` is an `fs_initcall`: on a cold boot, until it runs the regions
  are memblock-reserved and nothing is allocated from them.
- Migrate type on a KHO boot: `kho_init()` returns before that loop when a
  handover FDT exists; `kho_scratch_migratetype()` in
  `include/linux/kexec_handover.h` returns `MIGRATE_CMA` for scratch
  pageblocks when `mm/mm_init.c` initialises the memmap.
