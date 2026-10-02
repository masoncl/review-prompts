- `change_memory_common()`: accepts only a range inside one area from
  `find_vm_area()` whose flags have `VM_ALLOC` and not `VM_ALLOW_HUGE_VMAP`;
  a linear-map address gets `-EINVAL`.
- `-EINVAL` from `change_memory_common()`: no warning, and tested before
  `numpages == 0`, so a zero-page call on a bad address fails too.
- Linear alias: changed only when `rodata_full` is set and `set_mask` or
  `clear_mask` equals `PTE_RDONLY` exactly; `can_set_direct_map()` is not
  consulted.
- `rodata_full`: defaults to `true`; cleared by `rodata=off` and
  `rodata=noalias` in `arch_parse_debug_rodata()`.
- `can_set_direct_map()`: has no BBM capability term.
- `set_memory_valid()`: no range check; goes straight to
  `__change_memory_common()`.
- Range update: `update_range_prot()` uses
  `walk_kernel_page_table_range_lockless()` with `pageattr_ops`; arm64 has no
  `change_page_range()`.
- `update_range_prot()`: calls `split_kernel_leaf_mapping()` on every call; a
  non-zero return gives `WARN_ON_ONCE()` and no walk.
- `split_kernel_leaf_mapping()` returning 0 does not mean the range is split;
  see "BBM level capability" for the early returns.
- Leaf only partly covered at walk time: `pageattr_pud_entry()` and
  `pageattr_pmd_entry()` hit `WARN_ON_ONCE()` and return `-EINVAL`; the leaf
  is not changed.
- `pageattr_pte_entry()`: has no `PTE_CONT` test; a contiguous run that was
  not split is changed one entry at a time.
- **Potentially unsafe usage**: changing linear-map permissions from atomic
  context.
  - Unsafe: when `linear_map_requires_bbml3` is set, `system_supports_bbml3()`
    holds and the address is outside the KFENCE pool;
    `split_kernel_leaf_mapping()` then takes the mutex `pgtable_split_lock`
    and can allocate with `GFP_PGTABLE_KERNEL`.
  - Safe: a KFENCE pool address, as in `kfence_protect_page()`;
    `is_kfence_address()` returns before the mutex, and the pool is
    PTE-mapped by `arm64_kfence_map_pool()`, by `arch_kfence_init_pool()`, or
    with the rest of the linear map when `force_pte_mapping()` is true.
  - Safe: with `debug_pagealloc_enabled()`, as in `__kernel_map_pages()`;
    `force_pte_mapping()` is then true, so `linear_map_requires_bbml3` is
    false and the function returns before the mutex.
