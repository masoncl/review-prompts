- `kho_scratch_overlap()`: defined in `kernel/liveupdate/kexec_handover.c`
  and built whenever `CONFIG_KEXEC_HANDOVER` is on; there is no
  kernel/liveupdate/kexec_handover_debug.c in this tree.
- Stub that returns `false`: in `include/linux/kexec_handover.h`, for
  `CONFIG_KEXEC_HANDOVER` off, not for `CONFIG_KEXEC_HANDOVER_DEBUG` off.
- Debug gate: `IS_ENABLED(CONFIG_KEXEC_HANDOVER_DEBUG)` in front of the call,
  in `kho_preserve_folio()` and `kho_preserve_pages()` only; without the
  option nothing rejects an overlapping preserve.
- On overlap both return `-EINVAL`; `kho_preserve_pages()` tests the whole
  range once, before the first key is added.
- There is no __kho_preserve_order(), xa_load_or_alloc() or new_chunk() here;
  `kho_radix_alloc_node()`, which allocates the tracking tree pages, does not
  call `kho_scratch_overlap()`.
- `kho_preserve_vmalloc()`: no check of its own; each `kho_preserve_pages()`
  call inside it checks, under the same gate.
  - Data page in scratch: returns `-EINVAL`.
  - Chunk page in scratch: `new_vmalloc_chunk()` returns `NULL`, so the caller
    sees `-ENOMEM`.
- `kho_alloc_preserve()` on overlap, with the option: `ERR_PTR(-EINVAL)`,
  passed up from `kho_preserve_folio()`.
- Callers outside the debug gate: `kho_scratch_migratetype()` (memmap init)
  and `memblock_alloc_hugetlb()` in `mm/memblock.c`; a change to
  `kho_scratch_overlap()` changes both.
- Regions covered: only the entries of `kho_scratch[]`; ranges that
  `kho_extend_scratch()` marks with `memblock_mark_kho_scratch()` are not in
  the array and are not tested.
- **Potentially unsafe usage**: preserving a folio that came from a movable
  allocation.
  - Unsafe: when nothing has moved the folio out of `MIGRATE_CMA` pageblocks;
    `alloc_flags_cma()` in `mm/page_alloc.c` lets movable allocations take
    scratch pages, and the next kernel overwrites scratch.
  - Safe: after `memfd_pin_folios()`, as `memfd_luo_preserve_folios()` in
    `mm/memfd_luo.c` does; `folio_is_longterm_pinnable()` rejects
    `MIGRATE_CMA`, so the pin migrates such folios first.
- **Potentially unsafe usage**: preserving memory that was allocated from
  memblock during boot.
  - Unsafe: on a KHO boot, when the allocation was made without testing
    `kho_scratch_overlap()`; `choose_memblock_flags()` limits memblock to
    `MEMBLOCK_KHO_SCRATCH` ranges until `memblock_free_all()`.
  - Safe: when the allocator retries while `kho_scratch_overlap()` is true,
    as `memblock_alloc_hugetlb()` does.
