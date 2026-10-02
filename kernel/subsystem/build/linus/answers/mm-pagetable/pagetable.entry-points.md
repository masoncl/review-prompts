Rows not listed here (`folio_walk_start()`, `rmap_walk()`,
`change_protection()`, `apply_to_page_range()`) are where models expect them.

| Job | Start from |
|---|---|
| Map and lock a PTE table | `pte_offset_map_lock()` in `mm/pgtable-generic.c`; it is the out-of-line function itself. There is no __pte_offset_map_lock; the shared helper is `__pte_offset_map()` |
| Walk a range with callbacks | `walk_page_range()`. There is no walk_page_range_novma: kernel ranges use `walk_kernel_page_table_range()`, ptdump uses `walk_page_range_debug()` (`mm/internal.h`). Ops that set `install_pte` need `walk_page_range_mm_unsafe()` or `walk_page_range_vma_unsafe()` (`mm/internal.h`); the functions in `include/linux/pagewalk.h` return `-EINVAL` for them |
| Zap a range of one VMA | `zap_vma_range()`; see the name table below |
| Insert a PFN or a page from a driver | from `mmap` or a fault handler: for example `vmf_insert_pfn()`, `vmf_insert_mixed()`, `vm_insert_page()` and `remap_pfn_range()` in `mm/memory.c`. From an `mmap_prepare` hook: for example `mmap_action_remap()`, `mmap_action_ioremap()`, `mmap_action_simple_ioremap()` or `mmap_action_map_kernel_pages()` in `include/linux/mm.h`, carried out by `mmap_action_prepare()` and `mmap_action_complete()` in `mm/util.c` |
| Free the page tables of an unmapped range | `free_pgtables()`; it and `unmap_vmas()` take a `struct unmap_desc` (`mm/vma.h`). Callers: `unmap_region()` in `mm/vma.c`, `exit_mmap()` in `mm/mmap.c` |

Zap names; every name in the left column is defined nowhere in this tree:

| Name not in this tree | Does that job here |
|---|---|
| zap_page_range_single | `zap_vma_range()` (`include/linux/mm.h`) |
| zap_page_range_single_batched | `zap_vma_range_batched()` (`mm/internal.h`) |
| zap_vma_ptes | `zap_special_vma_range()`; accepts `VM_PFNMAP` or `VM_MIXEDMAP` |
| zap_vma_pages | `zap_vma()` |
| unmap_page_range, unmap_single_vma | static `__zap_vma_range()` in `mm/memory.c` |
| (OOM reaper zap) | `zap_vma_for_reaping()` (`mm/internal.h`) |
