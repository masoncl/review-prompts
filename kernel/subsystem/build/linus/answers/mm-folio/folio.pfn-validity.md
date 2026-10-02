- Without `CONFIG_MEMORY_HOTPLUG`: `pfn_to_online_page()` is a macro in
  `include/linux/memory_hotplug.h`, equal to `pfn_valid()` then
  `pfn_to_page()`; it adds nothing.
- `pfn_valid()` on an early section: returns 1 for every PFN of the section,
  since the test is `early_section(ms) || pfn_section_valid(ms, pfn)`.
- `pfn_to_online_page()`: applies `pfn_section_valid()` to early sections
  too, so it returns NULL for a hole in a boot-time section that
  `pfn_valid()` accepts.
- `pfn_section_valid()` without `CONFIG_SPARSEMEM_VMEMMAP`: a stub that
  returns 1.
- ZONE_DEVICE in `pfn_to_online_page()`: a section holding only device
  memory lacks `SECTION_IS_ONLINE` and fails `online_section()`. The
  `get_dev_pagemap()` lookup runs only when `online_device_section()` is
  true, that is `SECTION_IS_ONLINE` plus `SECTION_TAINT_ZONE_DEVICE`.
- `rcu_read_lock_sched()` in `pfn_valid()`: protects `ms->usage` only, which
  `section_deactivate()` in `mm/sparse-vmemmap.c` frees with `kfree_rcu()`.
  It does not keep the memmap alive after `pfn_valid()` returns.
- `pfn_valid()` not from `include/linux/mmzone.h`: under `CONFIG_FLATMEM` a
  range test against `max_mapnr` in `include/asm-generic/memory_model.h`;
  under `CONFIG_HAVE_ARCH_PFN_VALID` the arch supplies it, with sparsemem
  too, and `pfn_to_online_page()` calls it as an extra test.
- `pfn_to_page()` on an unchecked PFN: pointer arithmetic under
  `CONFIG_FLATMEM` and `CONFIG_SPARSEMEM_VMEMMAP`, so nothing fails before
  the first read of the page. Under `CONFIG_SPARSEMEM` alone it dereferences
  the `struct mem_section`, which `__nr_to_section()` may return as NULL.
- Validity granularity: one subsection under `CONFIG_SPARSEMEM_VMEMMAP`, one
  section otherwise; see `next_valid_pfn()`. `for_each_valid_pfn()` in
  `include/linux/mmzone.h` walks a range and rechecks at those boundaries.
- `pageblock_pfn_to_page()` is in `mm/page_alloc.h`; with `zone->contiguous`
  set it returns `pfn_to_page(start_pfn)` with no check.
- `isolate_migratepages_block()` calls `pfn_to_page()` per PFN, and
  `isolate_freepages_block()` calls it once and then steps the pointer, both
  with no test; they rely on their callers passing the block through
  `pageblock_pfn_to_page()` first.
