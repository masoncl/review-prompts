- `struct vm_area_struct` stores two page offsets: `vm_pgoff`, and an
  anonymous offset split across `__vm_anon_pgoff_lo` and, under
  `CONFIG_64BIT`, `__vm_anon_pgoff_hi`.
- Accessors in `include/linux/mm.h`: `vma_start_pgoff()` and
  `vma_start_anon_pgoff()`, each with an end and a last variant.

| Offset | Used by |
|---|---|
| `vm_pgoff` | file rmap tree key, `vma_filebacked_address()`, `linear_page_index()`, merge check for every VMA |
| anonymous offset | anon rmap tree key, `vma_anon_address()`, `linear_anon_page_index()`, anon `folio->index` in `__folio_set_anon()` |

- There is no vma_address(), vma_pgoff_address() or vma_pgoff_offset() here;
  `vma_filebacked_address()` and `vma_anon_address()` in `mm/internal.h` and
  `linear_page_delta()` in `include/linux/pagemap.h` do those jobs.
- `MAP_PRIVATE` file VMA: anon folios are indexed by the anonymous offset,
  not the file offset; `struct page_vma_mapped_walk` carries `pgoff_is_anon`
  to select which offset `vma_address_end()` uses.
- `vma_is_anonymous()` VMA with no `vm_file`, under `CONFIG_MMU`: the two
  offsets are equal; `linear_anon_page_index()` warns under
  `CONFIG_DEBUG_VM` if they differ.
- Initial anonymous offset: `addr >> PAGE_SHIFT`, set in `__mmap_region()`
  and `insert_vm_struct()` for file-backed VMAs too.
- `anon_vma_compatible()` needs both offsets contiguous in every case.
- Setters: `vma_set_pgoff()`, `vma_set_anon_pgoff()`, `vma_add_pgoff()`,
  `vma_sub_pgoff()` in `mm/vma.h`, `vma_set_range()` in `mm/vma.c`; each
  calls `vma_assert_can_modify()`, so an attached VMA must be write-locked.
- `vma_add_pgoff()` and `vma_sub_pgoff()` move both offsets;
  `vma_set_range()` takes both as arguments.
- `assert_sane_pgoff()`: under `CONFIG_DEBUG_VM` and `CONFIG_MMU`,
  `vma_set_pgoff()` warns when a `vma_is_anonymous()` VMA with no `vm_file`
  and no `anon_vma` gets an offset other than `vm_start >> PAGE_SHIFT`, so
  write `vm_start` first, as `__split_vma()` and `expand_downwards()` do.
- Move, faulted VMA: `copy_vma_and_data()` passes both offsets of the old
  address to `copy_vma()`, which keeps them.
- Move, `!vma->anon_vma`: `copy_vma()` resets the anonymous offset to
  `addr >> PAGE_SHIFT` for any VMA, and `vm_pgoff` too only when
  `vma_is_anonymous()`.
- `MREMAP_DONTUNMAP` of a whole VMA: `dontunmap_complete()` unlinks the old
  VMA's anon_vmas and resets its anonymous offset to
  `vm_start >> PAGE_SHIFT`, and `vm_pgoff` too only when `vma_is_anonymous()`
  and `vm_file` is NULL.
- **Unsafe usage**: moving `vm_start` of a VMA that is in an rmap tree and
  adjusting only one of the two offsets.
  - Unsafe: `avc_start_pgoff()` and `vma_anon_address()` use the anonymous
    offset, the file tree uses `vm_pgoff`; the stale one maps folios to
    wrong addresses.
  - Safe: `vma_add_pgoff()` or `vma_sub_pgoff()`, as `__split_vma()`,
    `vmg_adjust_set_range()` and `expand_downwards()` do.
  - Safe: `vma_set_range()` with both offsets, as `commit_merge()` does.
