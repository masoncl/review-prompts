- Assertion in `walk_kernel_page_table_range()`:
  `mmap_assert_locked(&init_mm)`; a read lock satisfies it.
- Without `CONFIG_LOCKDEP` the assertion only checks that somebody holds the
  rwsem, see `rwsem_assert_held_nolockdep()` in `include/linux/rwsem.h`.
- `walk_kernel_page_table_range_lockless()` in `mm/pagewalk.c`: does the
  walk and asserts nothing; `walk_kernel_page_table_range()` is the assertion
  plus a call to it.
- Callers in this tree: no function that calls
  `walk_kernel_page_table_range()` takes `get_online_mems()` itself;
  `ptdump_walk_pgd()` takes it, around `walk_page_range_debug()`.
- Lock order: `get_online_mems()` first, then the `init_mm` mmap lock, as in
  `ptdump_walk_pgd()`.
- Where the order is fixed: `memory_block_offline()` calls
  `mem_hotplug_begin()`, and `offline_pages()` then goes through
  `dissolve_free_hugetlb_folios()` to `vmemmap_remap_range()`, which takes
  `mmap_read_lock(&init_mm)`.
- `get_online_mems()`: an empty stub without `CONFIG_MEMORY_HOTPLUG`.
- **Potentially unsafe usage**: walking the linear map or vmemmap with only
  the `init_mm` mmap lock held.
  - Unsafe: while memory hot-remove can run on the memory that the range maps
    or describes; `arch_remove_memory()` frees the tables under
    `mem_hotplug_lock` only.
  - Safe: on an arch that does not select `ARCH_ENABLE_MEMORY_HOTPLUG`, as
    `arch_dma_set_uncached()` in `arch/openrisc/kernel/dma.c`.
  - Safe: with `get_online_mems()` held around the mmap lock, as
    `ptdump_walk_pgd()` does.
