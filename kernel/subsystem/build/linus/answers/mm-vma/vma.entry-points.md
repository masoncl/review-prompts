| Job | Start from | Easy to miss |
|---|---|---|
| Split | `vma_modify()` or `vms_gather_munmap_vmas()` in `mm/vma.c` | `split_vma()` and `__split_vma()` are both `static` in `mm/vma.c`; code outside that file gets a split only through the `vma_modify_flags()` family or an unmap, including the one `mmap_region()` does over existing mappings |
| Merge, existing VMA | `vma_modify()` | `vma_merge_existing_range()` is `static`; `vma_modify()` is its only caller in `mm/` |
| Merge, mremap copy | `vma_merge_copied_range()` in `mm/vma.c`, called from `copy_vma()` | moves `vmg->middle` to `vmg->copied_from`, then calls `vma_merge_new_range()` |
| Move a mapping | `do_mremap()` in `mm/mremap.c` | then `remap_move()`, `mremap_to()` or `mremap_at()`; `move_vma()` calls `copy_vma_and_data()`, which calls `copy_vma()` in `mm/vma.c` |
