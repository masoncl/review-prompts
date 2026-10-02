# MM Page Table Operations

## Main structures

### Objects and how they relate

- Split lock storage: `ALLOC_SPLIT_PTLOCKS` decides whether `ptl` in
  `struct ptdesc` is the lock itself or a pointer to it.
- `softleaf_t`: the decoded form of a non-present leaf. It is a typedef alias
  of `swp_entry_t` in `include/linux/mm_types.h`, so the two mix without a
  compiler error.
- `enum softleaf_type`: the kinds of non-present leaf; the one easy to forget
  is `SOFTLEAF_DEVICE_EXCLUSIVE`.
- `PT_kernel` in `pt_flags`: marks a table that maps the kernel; every caller
  of `ptdesc_set_kernel()` is in `include/asm-generic/pgalloc.h`.
- Deposited PTE tables for a huge PMD, except on powerpc hash: hang off
  `pmd_huge_pte` in the PMD table's `struct ptdesc` under
  `CONFIG_SPLIT_PMD_PTLOCKS`, otherwise off `pmd_huge_pte` in
  `struct mm_struct`; use the `pmd_huge_pte()` macro.
- Present leaf and `struct folio`: a present leaf need not map an accounted
  folio. `vm_normal_page()` in `mm/memory.c` returns NULL for special entries
  (`VM_PFNMAP`, `VM_MIXEDMAP`, the shared zero folios) when the VMA has no
  `find_normal_page`, and `zap_present_ptes()` then clears the entry with no
  rmap or refcount work.
- PTE table lifetime: an empty PTE table can be freed while its VMA stays
  mapped. `zap_pte_range()` does it under `CONFIG_PT_RECLAIM` when
  `reclaim_pt` is set in `struct zap_details`.
- `struct unmap_desc` in `mm/vma.h`: describes one teardown; `unmap_vmas()`
  and `free_pgtables()` take it in place of separate range arguments. It
  keeps the VMA range apart from the floor and ceiling within which tables
  may be freed.
- hugetlb shared PMD table: the number of extra sharers is `pt_share_count`
  in the table's `struct ptdesc`, present only under
  `CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`.
- hugetlb unsharing and `struct mmu_gather`: `huge_pmd_unshare()` takes the
  gather and records the unshare in it; `huge_pmd_unshare_flush()` completes
  the sequence. See `tlb_unshare_pmd_ptdesc()` in
  `include/asm-generic/tlb.h`.
- `struct lazy_mmu_state`: per-task nesting state for batched entry updates,
  embedded in `struct task_struct` under `CONFIG_ARCH_HAS_LAZY_MMU_MODE`.
- Lazy MMU in `mm/`: code brackets updates with `lazy_mmu_mode_enable()` and
  `lazy_mmu_mode_disable()` from `include/linux/pgtable.h`; nothing under
  `mm/` calls `arch_enter_lazy_mmu_mode()` directly.

## Where to look

**Core files:** Rows not listed here are where models expect them.

| Job | File in this tree |
|---|---|
| Map and lock a PTE table | `pte_offset_map_lock()` is declared in `include/linux/mm.h` and defined in `mm/pgtable-generic.c`; `pte_offset_map()` is an inline in `include/linux/mm.h`, not in `include/linux/pgtable.h` |
| Typed helpers for non-present entries | `include/linux/leafops.h` (`softleaf_from_pte()`, `softleaf_is_migration()`, `enum softleaf_type`); `softleaf_t` is a typedef of `swp_entry_t` in `include/linux/mm_types.h`. pte_to_swp_entry, is_swap_pte, is_migration_entry, is_pte_marker and non_swap_entry are defined nowhere |
| Swap entry encoding | `include/linux/swapops.h` holds `swp_entry()` and the constructors, for example `make_readable_migration_entry()`; there is no make_migration_entry. Type numbers (`SWP_MIGRATION_READ`, `SWP_PTE_MARKER`) are in `include/linux/swap.h` |
| Reverse-map walker | `mm/rmap.c` picks the VMAs; `mm/page_vma_mapped.c` walks inside one VMA; KSM folios go to `rmap_walk_ksm()` in `mm/ksm.c` |
| Reclaim of empty PTE tables | there is no mm/pt_reclaim.c and no try_to_free_pte. The code is static in `mm/memory.c`: `zap_pte_range()` calls `pte_table_reclaim_possible()`, `zap_empty_pte_table()` and `zap_pte_table_if_empty()`. In `mm/mmu_gather.c`, `CONFIG_PT_RECLAIM` selects the `call_rcu()` form of `__tlb_remove_table_one()`; the option is in `mm/Kconfig` |

**Entry points:** Rows not listed here (`folio_walk_start()`, `rmap_walk()`,
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

## Userfaultfd, soft-dirty and special bits

**The userfaultfd entry bit**

- Bit names: `_PAGE_UFFD` and `_PAGE_SWP_UFFD` on x86 and riscv, `PTE_UFFD`
  and `PTE_SWP_UFFD` on arm64. There is no _PAGE_UFFD_WP or
  _PAGE_SWP_UFFD_WP here.
- Accessor pattern, present: `pte_uffd()`, `pte_mkuffd()`,
  `pte_clear_uffd()`; the same three with `pmd_` and with `huge_pte_`.
- Accessor pattern, swap-format: `pte_swp_uffd()`, `pte_swp_mkuffd()`,
  `pte_swp_clear_uffd()`; the same three with `pmd_swp_`.
- No `pte_`, `pmd_` or `huge_pte_` accessor with a uffd_wp suffix exists;
  generic stubs are in `include/asm-generic/pgtable_uffd.h`.
- `pgtable_supports_uffd()`: the runtime test; there is no
  pgtable_supports_uffd_wp().
- `CONFIG_HAVE_ARCH_USERFAULTFD_WP` and `PTE_MARKER_UFFD_WP` keep the old
  spelling.
- `pte_is_uffd_wp_marker()` in `include/linux/leafops.h`: the marker test;
  `pte_swp_uffd_any()` is true for a non-present PTE with the swap bit or the
  marker, and only when `uffd_supports_wp_marker()`.
- Two modes use the bit: write-protect (`VM_UFFD_WP`, `userfaultfd_wp()`) and
  read-write-protect (`VM_UFFD_RWP`, `userfaultfd_rwp()`,
  `CONFIG_USERFAULTFD_RWP`, ioctl `UFFDIO_RWPROTECT`).
- `userfaultfd_register()`: returns `-EINVAL` for
  `UFFDIO_REGISTER_MODE_WP` together with `UFFDIO_REGISTER_MODE_RWP`, so a
  VMA is in at most one of the two modes.
- Mode of an entry: test the VMA and the bit together, with
  `userfaultfd_pte_wp()`, `userfaultfd_pte_rwp()`,
  `userfaultfd_huge_pmd_wp()` or `userfaultfd_huge_pmd_rwp()`;
  `userfaultfd_protected()` is true for either mode.
- `userfaultfd_rwp()`: constant false without
  `CONFIG_ARCH_HAS_PTE_PROTNONE`.
- Armed RWP present entry: the bit plus `PAGE_NONE`. In a
  `vma_is_accessible()` VMA, `handle_pte_fault()` sends a protnone entry to
  `do_uffd_rwp()` only if `userfaultfd_pte_rwp()`; otherwise to
  `do_numa_page()`.
- Protnone plus the bit in a `VM_UFFD_WP` VMA: a NUMA hint on a
  write-protected page, not RWP; see `numa_rebuild_large_mapping()`.
- `PTE_MARKER_UFFD_WP`: installed on a none entry by write-protect only;
  `userfaultfd_wp_use_markers()` is false for RWP, and `change_pte_range()`
  leaves a none PTE alone under `MM_CP_UFFD_RWP`.

**Soft-dirty support test**

- Generic accessor stubs in `include/linux/pgtable.h`: keyed on
  `CONFIG_HAVE_ARCH_SOFT_DIRTY`, not on `CONFIG_MEM_SOFT_DIRTY`. With the
  first set and the second off, the architecture's own accessors are used.
- `VM_SOFTDIRTY`: non-zero whenever `CONFIG_MEM_SOFT_DIRTY` is set, whatever
  the runtime test says.
- `VM_SOFTDIRTY` on a new VMA: set only under
  `pgtable_supports_soft_dirty()`; see `mm/vma.c` and `mm/vma_exec.c`.
- `vm_flags_init()`, `vm_flags_reset()`, `vm_flags_clear()`:
  `VM_WARN_ON_ONCE()` when passed `VM_SOFTDIRTY` on a system without
  support.
- `vma_soft_dirty_enabled()` in `mm/internal.h`: tests
  `pgtable_supports_soft_dirty()` first, because tracking is on when
  `VM_SOFTDIRTY` is clear.
- **Potentially unsafe usage**: taking `!pte_soft_dirty(pte)` or a clear
  `VM_SOFTDIRTY` to mean that the entry needs write-protection.
  - Unsafe: with no support test before it; without the bit every entry
    reads as "not yet soft-dirty", so every entry is kept write-protected.
  - Safe: behind `vma_soft_dirty_enabled()`, as `pte_needs_soft_dirty_wp()`
    and `pmd_needs_soft_dirty_wp()` do.
  - Safe: copying the bit from one entry to another with no test, as
    `do_swap_page()` does with `pte_swp_soft_dirty()` and
    `pte_mksoft_dirty()`; both are stubs without
    `CONFIG_HAVE_ARCH_SOFT_DIRTY`.
- `pte_to_pagemap_entry()` and `pagemap_page_category()` in
  `fs/proc/task_mmu.c`: report from `pte_soft_dirty()` with no support test.

**Special entries and normal-page lookup**

- There is no find_special_page() here; the hook is `find_normal_page` in
  `struct vm_operations_struct`, under `CONFIG_FIND_NORMAL_PAGE`.
- `find_normal_page`: called only for a special entry at a level that has a
  special bit; it runs before the VMA flag tests and its result is returned
  as is.
- `__vm_normal_page()`: does not limit `find_normal_page` to PTEs; that it
  is used for PTEs only is a property of the one implementor,
  `gntdev_vma_find_normal_page()` in `drivers/xen/gntdev.c`.
- `pgtable_level_has_pxx_special()` in `mm/memory.c`: decides per level.
  PTE uses `CONFIG_ARCH_HAS_PTE_SPECIAL`, PMD
  `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP`, PUD `CONFIG_ARCH_SUPPORTS_PUD_PFNMAP`.
- Architecture with a PTE special bit and no
  `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP`: `vm_normal_page_pmd()` uses the VMA
  flag rules, with `linear_page_index()` of the PMD address.
- VMA flag rules, order: `VM_MIXEDMAP` is tested first and uses only
  `pfn_valid()`; the `vm_pgoff` compare and `vma_is_cow_mapping()` apply to
  `VM_PFNMAP` without `VM_MIXEDMAP`.
- Zero PFN and huge zero PFN at a level with a special bit: recognised only
  through the special bit. A non-special entry with such a PFN reaches
  `VM_WARN_ON_ONCE()` and is returned as a normal page.

**Marking entries special**

- `insert_pmd()` folio path: takes the reference with `folio_get()`, the
  rmap with `folio_add_file_rmap_pmd()`, and the counter with
  `add_mm_counter()`.
- `insert_pmd()` with the huge zero folio: `folio_mk_pmd()` then
  `pmd_mkspecial()`, and no reference, rmap or counter. `insert_pud()` has
  no such branch.
- `insert_page_into_pte_locked()` with a zero folio: `mk_pte()` then
  `pte_mkspecial()`, and no reference, rmap or counter.
- `insert_pmd()` and `insert_pud()`: the `prot` argument is used only on the
  PFN path; the folio path uses `vma->vm_page_prot`.
- `folio_mk_pmd()` is `pmd_mkhuge(pfn_pmd())`; `folio_mk_pud()` is
  `pud_mkhuge(pfn_pud())`; see `include/linux/mm.h`.
- `pmd_mkspecial()` and `pud_mkspecial()`: return the entry unchanged
  without `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP` and
  `CONFIG_ARCH_SUPPORTS_PUD_PFNMAP`; `pmd_special()` and `pud_special()` are
  then constant false.
- The three `BUG_ON()`s shared by `vmf_insert_pfn_pmd()`,
  `vmf_insert_pfn_pud()` and `vmf_insert_pfn_prot()`: in a `VM_PFNMAP` VMA
  they keep a raw PFN recognisable by the VMA rules of `__vm_normal_page()`
  at a level with no special bit.
- **Unsafe usage**: `pmd_mkspecial()`, `pud_mkspecial()` or `pte_mkspecial()`
  on an entry for which a reference, an rmap or an mm counter was taken.
  `zap_huge_pmd()` gets NULL from `vm_normal_folio_pmd()` and drops none of
  them.
  - Safe: special on a folio-built entry only for the zero folios, with no
    reference, rmap or counter taken for the entry, as
    `set_huge_zero_folio()` does.
- **Potentially unsafe usage**: a special entry in a VMA with neither
  `VM_PFNMAP` nor `VM_MIXEDMAP`.
  - Unsafe: for any PFN other than the zero PFNs, when the VMA has no
    `find_normal_page`; `__vm_normal_page()` calls `print_bad_page_map()`,
    which taints the kernel.
  - Safe: the zero PFN or the huge zero folio, as `do_anonymous_page()` and
    `set_huge_zero_folio()` do; `__vm_normal_page()` tests `is_zero_pfn()`
    and `is_huge_zero_pfn()`.
- **Potentially unsafe usage**: a raw-PFN entry, with no reference taken, for
  a `pfn_valid()` PFN in a `VM_MIXEDMAP` VMA.
  - Unsafe: at a level with no special bit, for a PFN other than the zero
    PFNs; `__vm_normal_page()` returns the page as normal and zap drops a
    reference and an rmap nobody took.
  - Safe: at a level with a special bit, through `insert_pfn()`, which sets
    `pte_mkspecial()`; `__vm_normal_page()` returns NULL for a special entry
    in a `VM_MIXEDMAP` VMA that has no `find_normal_page`.
  - Safe: without a PTE special bit, inserting the page refcounted, as
    `__vm_insert_mixed()` does with `insert_page()`;
    `vmf_insert_pfn_prot()` has a `BUG_ON()` for this case.
- **Potentially unsafe usage**: using `pmd_special()` or `pud_special()`
  alone to find PFN maps.
  - Unsafe: when a leaf that the test misses is then used as a refcounted
    folio; the test is constant false where the level has no special bit.
  - Safe: `copy_huge_pmd()`; a PFN leaf it misses is in a VMA with `vm_ops`,
    and it returns 0 for a VMA that fails `vma_is_anonymous()` before it
    touches the page.
  - Safe: `vm_normal_page_pmd()`, `vm_normal_folio_pmd()` or
    `vm_normal_page_pud()`, which fall back to the VMA rules.

**Clearing userfaultfd protection from entries**

- `userfaultfd_clear_vma()`: does not call `uffd_wp_range()`; it calls
  `change_protection()` itself, when `userfaultfd_protected(vma)`.
- Flags passed: `MM_CP_UFFD_WP_RESOLVE` for a `VM_UFFD_WP` VMA,
  `MM_CP_UFFD_RWP_RESOLVE` for a `VM_UFFD_RWP` VMA, plus
  `MM_CP_TRY_CHANGE_WRITABLE` when `vma_wants_manual_pte_write_upgrade()`.
- `VM_UFFD_RWP` VMA: besides the bit, the `PAGE_NONE` protection must go;
  the same walk rewrites each present entry to `vma->vm_page_prot`.
- `vma_modify_flags_uffd()` and `userfaultfd_set_vm_flags()`: clear neither
  the bit nor `PAGE_NONE` from any entry; they only split or merge and
  change the VMA.
- `change_huge_pud()`: `WARN_ON_ONCE()` and skips for any uffd flag; there
  is no pud_uffd() or pud_mkuffd() here.
- `change_protection()`: `WARN_ON_ONCE()` and does nothing if WP and RWP
  flags are mixed, or a protect flag comes with its resolve flag.
- `userfaultfd_register()`: returns `-EBUSY` for a registration to the same
  context that would drop `VM_UFFD_WP` or `VM_UFFD_RWP` from a VMA; the
  mode can only change through unregister, hence through
  `userfaultfd_clear_vma()`.
- **Potentially unsafe usage**: clearing `VM_UFFD_WP` or `VM_UFFD_RWP` with
  `userfaultfd_reset_ctx()` directly.
  - Unsafe: when entries of the VMA still carry the bit, `PAGE_NONE` or a
    `PTE_MARKER_UFFD_WP`; a later registration reads them in its own mode,
    and `change_present_ptes()` turns a leftover bit into `PAGE_NONE` in a
    `VM_UFFD_RWP` VMA.
  - Safe: in `dup_userfaultfd()` on the child VMA before
    `copy_page_range()`; `__copy_present_ptes()` and `copy_pte_marker()`
    test the destination VMA and drop the bit and the marker.
  - Safe: through `userfaultfd_clear_vma()`, which walks `[start, end)`
    first.

**Userfaultfd state after a move**

- `mremap_userfaultfd_prep()`: defined in `mm/userfaultfd.c`; there is no
  fs/userfaultfd.c in this tree.
- `mremap_userfaultfd_prep()`: takes no range. Without
  `UFFD_FEATURE_EVENT_REMAP` it calls `userfaultfd_reset_ctx()` on the whole
  VMA, which clears `vm_userfaultfd_ctx` and all of `__VM_UFFD_FLAGS`.
- `copy_vma_and_data()` in `mm/mremap.c`: calls it after
  `move_page_tables()`, and only when the move succeeded.
- `move_page_tables()`: writes only `[new_addr, new_addr + old_len)` of the
  returned VMA.
- `copy_vma()`: returns either a fresh `vm_area_dup()` copy or an existing
  neighbour expanded by `vma_merge_copied_range()`.
- `is_mergeable_vma()` in `mm/vma.c`: compares the VMA flags and the context
  pointer; nothing on the merge path tests `UFFD_FEATURE_EVENT_REMAP`.
- `move_ptes()`, `move_huge_pmd()`, `move_huge_pte()`: read
  `vma_has_uffd_without_event_remap()` from the source VMA; when true they
  clear the bit, and for a present RWP entry restore `vma->vm_page_prot`.
  `move_ptes()` and `move_huge_pte()` also drop a `PTE_MARKER_UFFD_WP`.
- `uffd_supports_page_table_move()`: refuses `move_normal_pmd()` and
  `move_normal_pud()` if either VMA has a context without
  `UFFD_FEATURE_EVENT_REMAP`, so that the walk reaches every leaf entry.
- **Potentially unsafe usage**: resetting the context of the whole VMA that
  `copy_vma()` returned.
  - Unsafe: when that VMA covers populated addresses outside the moved
    range, as after a merge with a registered neighbour; those entries keep
    the bit, `PAGE_NONE` or the marker in a VMA with no uffd flag.
  - Safe: when `copy_vma()` took the `vm_area_dup()` branch; every populated
    entry of the new VMA was written by the move helpers above.
  - Safe: cleaning a range and then resetting only that range, as
    `userfaultfd_clear_vma()` does with `change_protection()` and
    `vma_modify_flags_uffd()`.

**Soft dirty on move**

- `move_ptes()`: clears the old entries with `get_and_clear_ptes()` only; it
  does not call `ptep_get_and_clear()`.
- `move_ptes()`: the earlier `ptep_get()` value is used for the none and
  present tests and for batching; the entry written is the one
  `get_and_clear_ptes()` returned.
- Large-folio batch: `get_and_clear_ptes()` ORs dirty and young over the
  batch, and `set_ptes()` writes that to every entry, so a clean entry can
  arrive dirty. Dirty is never dropped.
- `mremap_folio_pte_batch()`: batches with `FPB_RESPECT_WRITE` only, so
  entries that differ in dirty or soft-dirty share a batch.
- `force_flush` in `move_ptes()` and `move_huge_pmd()`: set for any present
  old entry, dirty or not.
- `move_soft_dirty_pmd()` in `mm/huge_memory.c`: under
  `pgtable_supports_soft_dirty()` it marks a present PMD and a migration
  entry (`pmd_is_migration_entry()`); other non-present PMDs are left as
  they are.
- `move_present_ptes()` in `mm/userfaultfd.c`: builds a new entry with
  `folio_mk_pte()`, so it sets soft-dirty under
  `pgtable_supports_soft_dirty()` and copies dirty from the source with
  `pte_dirty()`.

## Present entry state

**Writable and dirty combinations**

- `can_change_pte_writable()`: common vetoes are in
  `maybe_change_pte_writable()`; the mapping-specific halves are
  `can_change_private_pte_writable()` and `can_change_shared_pte_writable()`.
- mprotect does not call `can_change_pte_writable()`; see
  `set_write_prot_commit_flush_ptes()` in `mm/mprotect.c`.
- `VM_PFNMAP` and `VM_MIXEDMAP`: no exemption. Private: `vm_normal_page()`
  returns NULL for a special entry when the VMA has no `find_normal_page`, so
  that entry is never upgraded. Shared: `pte_dirty()` decides.
- Shared writable VMA where `vma_wants_writenotify()` is false: `vm_page_prot`
  is already writable, so writable-and-clean is legal; `set_pte_range()` sets
  dirty on a read fault only if `folio_test_dirty()`.
- Zero page: the `VM_WARN_ON_ONCE()` against a dirty zero-page entry is in
  `can_change_shared_pte_writable()` only. In a private VMA `replace_page()` in
  `mm/ksm.c` maps the zero page dirty as a marker; `is_ksm_zero_pte()` tests it.
- Anonymous fault: `map_anon_folio_pte_nopf()` sets write and dirty together,
  and only when the VMA has `VM_WRITE`.
- x86: Write=0 with Dirty=1 is the shadow-stack encoding. `pte_wrprotect()`
  moves dirty to `_PAGE_SAVED_DIRTY`, `pte_dirty()` tests both bits, and
  `pte_mkwrite()` picks the encoding from `VM_SHADOW_STACK`.
- **Unsafe usage**: deciding the write upgrade for a batch of entries of one
  anon large folio from `PageAnonExclusive()` of the first page.
  - Safe: split the batch into runs of equal exclusivity, as
    `commit_anon_folio_batch()` does.

**Accessed with dirty**

- There is no do_set_pte() here; `set_pte_range()` in `mm/memory.c` installs
  file and shmem entries.
- `set_pte_range()` calls `pte_sw_mkyoung()`, not `pte_mkyoung()`.
- `pte_sw_mkyoung()`: only `arch/mips` defines it as `pte_mkyoung()`; the
  generic one in `include/linux/pgtable.h` returns the entry unchanged.
- Anonymous fault: `pte_sw_mkyoung()` is called in `map_anon_folio_pte_nopf()`,
  not in `do_anonymous_page()`.
- `ptep_set_access_flags()` on x86 (`arch/x86/mm/pgtable.c`): writes the entry
  only when `dirty` is non-zero, so the `pte_mkyoung()` in `handle_pte_fault()`
  is not stored on a read fault.
- There is no is_migration_entry_young() here; `remove_migration_pte()` tests
  `softleaf_is_migration_young()` from `include/linux/leafops.h`.

**Lazily freed entries**

- Write bit: `madvise_free_pte_range()` leaves it untouched; only accessed and
  dirty are cleared.
- Next write without hardware dirty tracking: `handle_pte_fault()` finds
  `pte_write()` true and sets dirty; `do_wp_page()` is not called.
- Reclaim side for a PTE-mapped folio lives in `ttu_anon_folio()` and
  `ttu_anon_lazyfree_folio()` in `mm/rmap.c`, reached from
  `try_to_unmap_one()`.
- `ttu_anon_lazyfree_folio()` order: dirty test first, refcount test second.
- Dirty folio, VMA not `VM_DROPPABLE`: `folio_set_swapbacked()`, return false.
- Clean folio with `ref_count != 1 + map_count`: returns false and does not
  call `folio_set_swapbacked()`; the folio stays lazyfree.
- `VM_DROPPABLE`: skips only the dirty test; the refcount test still applies.
- On false, `try_to_unmap_one()` restores the entries with `set_ptes()` and
  aborts the walk.
- Large lazyfree folios are unmapped as a batch (`folio_unmap_pte_batch()`);
  `get_and_clear_ptes()` returns dirty merged over the batch, so one dirty
  entry keeps the whole folio.
- `folio_mark_lazyfree()` is in `mm/folio.c` and only queues the folio;
  `lru_lazyfree()` clears swapbacked when the batch drains.

**NUMA and userfaultfd protnone entries**

- Two mechanisms: NUMA hinting (`MM_CP_PROT_NUMA`) and userfaultfd RWP
  (`VM_UFFD_RWP`, `MM_CP_UFFD_RWP`, `mrwprotect_range()` in
  `mm/userfaultfd.c`). `change_protection()` uses `PAGE_NONE` for both.
- `CONFIG_USERFAULTFD_RWP` off: `VM_UFFD_RWP` is `VM_NONE`. Without
  `CONFIG_ARCH_HAS_PTE_PROTNONE`, `userfaultfd_rwp()` returns false.
- RWP entry: `pte_protnone()` plus `pte_uffd()` in a VMA with `VM_UFFD_RWP`;
  test with `userfaultfd_pte_rwp()` or `userfaultfd_huge_pmd_rwp()`.
- Any other protnone entry in an accessible VMA is a NUMA hint, including
  protnone plus uffd bit in a `VM_UFFD_WP` VMA: the scan keeps the bit.
- `handle_pte_fault()`: `do_uffd_rwp()` for RWP, else `do_numa_page()`. The PMD
  twin is `do_huge_pmd_uffd_rwp()`.
- `userfaultfd_pte_wp()` tests `userfaultfd_wp()`, so it is false in RWP VMAs.
- Non-present entries carry only the bit (`pte_swp_uffd()`); the protection is
  derived again when the entry becomes present.
- NUMA state is not kept across a rebuild: `__split_huge_pmd_locked()` and
  `remove_migration_pte()` build from `vma->vm_page_prot`.
- `change_present_ptes()`: reapplies `PAGE_NONE` after `pte_modify()` when the
  entry has the bit in an RWP VMA, so mprotect cannot disarm it.
- **Potentially unsafe usage**: building a present entry from
  `vma->vm_page_prot` and carrying the uffd bit over with `pte_mkuffd()`.
  - Unsafe: in a VMA where `userfaultfd_rwp()` is true, when the old entry
    can be RWP-armed (non-present with the bit, or protnone with the bit),
    without `pte_modify(pte, PAGE_NONE)`; the next access does not trap.
  - Safe: `pte_mkuffd()` then `pte_modify(pte, PAGE_NONE)`, as `do_swap_page()`
    and `__split_huge_pmd_locked()` do. Search `mm/` for `PAGE_NONE` for the
    rest.
  - Safe: `wp_page_copy()`, where the old entry is present and, in an
    accessible VMA, never protnone: `handle_pte_fault()` sends every protnone
    entry of an accessible VMA elsewhere before `do_wp_page()`, and
    `do_swap_page()` skips `do_wp_page()` for a restored RWP entry.
- **Unsafe usage**: clearing the uffd bit of an RWP entry and leaving
  `PAGE_NONE`; the entry then faults as a NUMA hint.
  - Safe: `pte_modify()` to the `vm_page_prot` of the VMA, then
    `pte_clear_uffd()`, as `__copy_present_ptes()` and `move_ptes()` in
    `mm/mremap.c` do.
- **Unsafe usage**: a NUMA rebuild that rewrites every protnone entry it finds.
  - Safe: skip entries with `userfaultfd_rwp(vma) && pte_uffd()`, as
    `numa_rebuild_large_mapping()` does.

**NUMA scan of no-access entries**

- The skip is in `change_pte_range()`, before `change_present_ptes()` is
  called; `change_present_ptes()` has no such test.
- Skipped entries are not added to the returned count.
- RWP-armed entries are protnone too, so the scan leaves them alone.
- `MM_CP_UFFD_RWP` skips only protnone entries that already have the uffd bit;
  a NUMA-hint entry is rewritten to add the bit.
- There is no prot_numa_skip() here; the folio filter is
  `folio_can_map_prot_numa()` in `mm/mempolicy.c`, applied only under
  `MM_CP_PROT_NUMA`.
- Top-tier folios: skipped when `NUMA_BALANCING_NORMAL` is clear in
  `sysctl_numa_balancing_mode`.

**Writable entries and VM_WRITE**

- `FAULT_FLAG_WRITE` does not imply `VM_WRITE`: `FOLL_FORCE` write faults reach
  `wp_page_reuse()` and `wp_page_copy()` in a VMA without it. `maybe_mkwrite()`
  then leaves the entry dirty and read-only.
- The page table lock does not hold `vm_flags` stable. `mprotect_fixup()`
  rewrites them under the mmap write lock and `vma_start_write()`, then calls
  `change_protection()`.
- Rmap walks take neither lock for the VMAs they visit; their callbacks in
  `mm/rmap.c`, `mm/migrate.c` and `mm/ksm.c` do not test `VM_WRITE`.
- `remove_migration_pte()`: calls `pte_mkwrite()` when
  `softleaf_is_migration_write()`; it does not call `maybe_mkwrite()`. There is
  no is_writable_migration_entry() here.
- `__split_huge_pmd_locked()`: takes `write` from `pmd_write()`,
  `softleaf_is_migration_write()` or `softleaf_is_device_private_write()`,
  with no `VM_WRITE` test.
- Saved write state is downgraded in `change_softleaf_pte()` in
  `mm/mprotect.c`, `change_non_present_huge_pmd()` in `mm/huge_memory.c` and,
  for hugetlb, `hugetlb_change_protection()` in `mm/hugetlb.c`.
- The downgrade is unconditional: every `change_protection()` pass, NUMA scan
  and userfaultfd included, turns writable migration entries read-only.
- `can_change_pte_writable()` result: valid only under the same page table
  lock hold. `do_numa_page()` drops it once it unlocks (`ignore_writable`).
- **Potentially unsafe usage**: `pte_mkwrite()` on a new entry in place of
  `maybe_mkwrite()`.
  - Unsafe: when the write bit comes neither from saved state nor from
    `vma->vm_page_prot`, and nothing on the path has tested `VM_WRITE` under
    the mmap lock or VMA lock; the entry is then writable in a VMA without
    `VM_WRITE`.
  - Safe: after an explicit test, as `map_anon_folio_pte_nopf()` does.
  - Safe: `move_present_ptes()`, since `validate_move_areas()` rejects VMAs
    without `VM_WRITE`.
  - Safe: when the entry built from `vma->vm_page_prot` is already
    `pte_write()`, as in `do_numa_page()`; `vma_set_page_prot()` derives
    `vm_page_prot` from the VMA flags.
  - Safe: from saved state under the page table lock, as
    `remove_migration_pte()` does; `change_softleaf_pte()` downgrades that
    state under the same lock when the protection changes.
- **Unsafe usage**: a new kind of saved write state that
  `change_softleaf_pte()` does not downgrade; `remove_migration_pte()` and
  `__split_huge_pmd_locked()` set the write bit from saved state with no
  `VM_WRITE` test.
  - Safe: a kind that `change_softleaf_pte()` rewrites to its read form, as
    it does for `softleaf_is_migration_write()` and
    `softleaf_is_device_private_write()` entries;
    `change_non_present_huge_pmd()` does the same for PMDs.

**Reading and writing entries**

- `ptep_get_lockless()` is overridden in two places: under
  `CONFIG_GUP_GET_PXX_LOW_HIGH` in `include/linux/pgtable.h`, and on arm64
  under `CONFIG_ARM64_CONTPTE`.
- arm64 `ptep_get()` under `CONFIG_ARM64_CONTPTE`: expects the page table
  lock; `contpte_ptep_get()` reads the neighbours with no consistency check.
- `contpte_ptep_get_lockless()` retries until the whole block is consistent, so
  a lockless read on arm64 needs `ptep_get_lockless()` even though the entry is
  one word.
- Elsewhere `ptep_get_lockless()` is `ptep_get()`, so a wrong choice does not
  fail on x86-64.
- `handle_pte_fault()`: reads `vmf->orig_pte` with `ptep_get_lockless()`; code
  that then rewrites the entry compares it with `pte_same()` after taking the
  lock, for example `handle_pte_fault()` itself, `do_numa_page()` and the
  async branch of `do_uffd_rwp()`.

**Direct read of a PTE**

- Generic code under `mm/` has no direct read of a PTE slot; every
  `*ptentp` or `*entry` there points to a copy.
- **Potentially unsafe usage**: dereferencing a `pte_t *`.
  - Unsafe: in generic code when the pointer is a page table slot; the read
    skips the `ptep_get()` override of the architecture.
  - Safe: the pointer is a copy that `ptep_get()` filled, as `ptentp` in
    `folio_pte_batch_flags()` in `mm/internal.h`, which warns if it points into
    a page table.
  - Safe: architecture code whose `ptep_get()` is the generic one, under the
    page table lock, as x86 `ptep_set_access_flags()` in
    `arch/x86/mm/pgtable.c`.
  - Safe: the private accessor of the architecture, as arm64 `__ptep_get()`.
- `ptep_get()` overrides: search `arch/` for `define ptep_get`; arm64 with
  `CONFIG_ARM64_CONTPTE` and powerpc 8xx with `CONFIG_PPC_16K_PAGES` return
  more than the raw word.

**Atomic updates**

- `ptep_modify_prot_start()` does not always clear the entry: Xen PV
  (`xen_ptep_modify_prot_start()`) returns `*ptep` and leaves it present; the
  commit preserves accessed and dirty with `MMU_PT_UPDATE_PRESERVE_AD`.
- Code between start and commit must not assume the entry is non-present.
- arm64 hardware dirty: the CPU clears `PTE_RDONLY` on an entry with
  `PTE_WRITE`; `pte_write()` does not change.
- mprotect start/commit user: `change_present_ptes()`, through
  `prot_commit_flush_ptes()`.

**Comparing page contents**

- `try_to_map_unused_to_zeropage()` in `mm/migrate.c`: compares with
  `pages_identical(page, ZERO_PAGE(0))`; it does not call `memchr_inv()`.
- Its refusals: `PageCompound()`, `PageHWPoison()`, `folio_test_mlocked()`,
  `VM_LOCKED`, `mm_forbids_zeropage()`. It has no userfaultfd test and no MTE
  test of its own.
- It keeps the uffd bit (`pte_mkuffd()`) and reapplies `PAGE_NONE` for RWP.
- Stability there: the entry is not present and the page is locked;
  `VM_BUG_ON_PAGE()` asserts both.
- It runs after every successful split of an anon folio that is not
  device-private (`TTU_USE_SHARED_ZEROPAGE`), not only for underused folios.
- arm64 `memcmp_pages()` in `arch/arm64/kernel/mte.c`: equal data with either
  page `page_mte_tagged()` compares as different, unless both are the same
  page.
- Another caller: `orig_page_is_identical()` in `kernel/events/uprobes.c`;
  `__uprobe_write()` compares after `ptep_clear_flush()` and a refcount test.
- **Unsafe usage**: deciding to replace a page in a user mapping with a byte
  compare that is not `memcmp_pages()`; on arm64 the tags are lost.
  - Safe: `pages_identical()`, as `try_to_merge_one_page()` does; a checksum
    such as `calc_checksum()` only as a filter before it.

## Non-present entries

**Typed non-present entries**

- Old swap-entry predicates: defined nowhere in this tree (for example
  is_swap_pte(), is_migration_entry(), is_pfn_swap_entry(), non_swap_entry(),
  pte_to_swp_entry(), is_pte_marker()); of that family only
  `is_hwpoison_entry()` remains in `include/linux/swapops.h`.
- Kind predicates on a present or empty entry: all false, so no
  `pte_present()` test is needed before a kind test; `check_pte()` in
  `mm/page_vma_mapped.c` decodes a possibly-present PTE under
  `PVMW_MIGRATION` and relies on this.
- `softleaf_is_none()`: true for both present and empty; it cannot tell them
  apart.
- `softleaf_type()`: returns `SOFTLEAF_NONE` after `VM_WARN_ON_ONCE()` for a
  type number it does not know; `softleaf_is_none()` is false for that same
  entry.
- `softleaf_from_pmd()`: real only under `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`,
  otherwise it returns the none value for every PMD; there is no
  CONFIG_ARCH_ENABLE_THP_MIGRATION here.
- `pmd_is_device_private_entry()`: a `false` stub unless both
  `CONFIG_ZONE_DEVICE` and `CONFIG_ARCH_HAS_PMD_SOFTLEAVES` are set.
- Predicates easy to miss: `softleaf_is_migration_young()`,
  `softleaf_is_migration_dirty()`, `pte_is_uffd_marker()` (uffd-wp or poison
  marker), `softleaf_is_valid_pmd_entry()`.
- Encoders: `softleaf_to_pte()` and `softleaf_to_pmd()` wrap
  `swp_entry_to_pte()` and `swp_entry_to_pmd()`; both spellings are in use.

**Kinds of non-present entry**

| Kind | Folio ref + mapcount | PMD can hold it |
|---|---|---|
| `SOFTLEAF_NONE` | not an entry; also what `softleaf_type()` gives for an unknown type | no |
| `SOFTLEAF_SWAP` | neither; it holds a swap count | no |
| `SOFTLEAF_MIGRATION_READ`, `SOFTLEAF_MIGRATION_READ_EXCLUSIVE`, `SOFTLEAF_MIGRATION_WRITE` | neither; `try_to_migrate_one()` removes the rmap and puts the folio after installing the entry | yes |
| `SOFTLEAF_DEVICE_PRIVATE_READ`, `SOFTLEAF_DEVICE_PRIVATE_WRITE` | both | yes |
| `SOFTLEAF_DEVICE_EXCLUSIVE` | both | no |
| `SOFTLEAF_HWPOISON` | neither | no |
| `SOFTLEAF_MARKER` | neither | no |

- PMD kinds, outside hugetlb: `softleaf_is_valid_pmd_entry()` accepts
  migration and device-private only; a PMD decodes to either only under
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`.
- `zap_nonpresent_ptes()`, migration entry: decrements `rss[mm_counter(folio)]`
  only; it does not call `folio_remove_rmap_pte()` or `folio_put()`.
- `zap_nonpresent_ptes()`, swap entry: releases with
  `swap_put_entries_direct()`; there is no free_swap_and_cache_nr() here.
- `zap_nonpresent_ptes()`, uffd-wp marker: dropped unconditionally in an
  anonymous VMA; kept in any other VMA unless `zap_drop_markers()`.
- `zap_nonpresent_ptes()`, hwpoison entry and poison marker: cleared unless
  `should_zap_cows()` is false.
- `details == NULL`: `zap_drop_markers()` is false and `should_zap_cows()` is
  true, so guard markers and file uffd-wp markers stay and poison goes.

**Dispatching on kind**

- **Potentially unsafe usage**: calling `softleaf_to_pfn()`,
  `softleaf_to_page()` or `softleaf_to_folio()` with no kind test in the same
  function.
  - Unsafe: when the entry can be swap, marker or none; the offset is then a
    swap slot, marker bits or 0, and the only check is
    `VM_WARN_ON_ONCE(!softleaf_has_pfn(entry))`, which is compiled out without
    `CONFIG_DEBUG_VM`.
  - Safe: after a specific predicate, as `check_pte()` does with
    `softleaf_is_migration()` under `PVMW_MIGRATION`, and with
    `softleaf_is_device_private()` or `softleaf_is_device_exclusive()`
    otherwise.
  - Safe: on an entry returned by `page_vma_mapped_walk()`, as
    `try_to_migrate_one()` and `remove_migration_pte()` do; `check_pte()` has
    already rejected every other non-present kind.
  - Safe: when the only caller made the test, as
    `try_restore_exclusive_pte()` in `mm/memory.c`, which
    `copy_nonpresent_pte()` calls after `softleaf_is_device_exclusive()`.
- Migration entry at fork: the only accounting in `copy_nonpresent_pte()` is
  `rss[mm_counter(folio)]++`; it takes no reference and no rmap, because the
  entry owns none.
- Swap entry at fork: the count is taken with `swap_dup_entry_direct()`;
  failure makes `copy_nonpresent_pte()` return `-EIO`. There is no
  swap_duplicate() here.
- Waiting on a migration or device-private entry: see "Folio behind a
  migration entry".

**Marker entries**

- Swap-in error: there is no separate swap-error marker;
  `make_poisoned_swp_entry()` builds a `PTE_MARKER_POISONED` marker, so the
  fault returns `VM_FAULT_HWPOISON`.
- `pte_marker_handle_uffd_wp()`: when the VMA is not `userfaultfd_wp()` it
  calls `pte_marker_clear()`, which clears the PTE only if it still equals
  `vmf->orig_pte`, and returns 0; otherwise `do_pte_missing()`.
- uffd-wp markers are write-protect only: `copy_pte_marker()` and
  `pte_marker_handle_uffd_wp()` test `userfaultfd_wp()`, not
  `userfaultfd_protected()`; a VMA with only `VM_UFFD_RWP` gets no uffd-wp
  marker copied and clears one on fault.
- hugetlb fault: `hugetlb_fault()` tests the marker itself and does not call
  `handle_pte_marker()`; poison gives `VM_FAULT_HWPOISON_LARGE`, guard gives
  `WARN_ON_ONCE()` plus `VM_FAULT_SIGSEGV`, anything else goes to
  `hugetlb_no_page()`.
- Zap without `ZAP_FLAG_DROP_MARKER`:

| Marker | Survives |
|---|---|
| uffd-wp, anonymous VMA | no, always dropped |
| uffd-wp, other VMA | yes |
| guard | yes |
| poison | only when `should_zap_cows()` is false |

- `cond_install_uffd_wp_ptes()` in `mm/memory.c`: installs the uffd-wp marker
  after a clear, only in a non-anonymous `userfaultfd_wp()` VMA and only when
  the old entry carried the uffd bit or was a uffd-wp marker; there is no
  pte_install_uffd_wp_if_needed() here.
- `vma_needs_copy()`: true when `dst_vma` has any `VM_COPY_ON_FORK` flag
  (`VM_PFNMAP`, `VM_MIXEDMAP`, `VM_UFFD_WP`, `VM_UFFD_RWP`, `VM_MAYBE_GUARD`)
  or `src_vma->anon_vma` is set; otherwise no entry, marker or not, is copied.

**Folio behind a migration entry**

- `softleaf_to_folio()` kind check: `VM_WARN_ON_ONCE(!softleaf_has_pfn(entry))`,
  so a hwpoison entry passes as well.
- Lock check: `softleaf_migration_sync()` does
  `VM_WARN_ON_ONCE(!folio_test_locked(folio))` for migration entries only;
  there is no `BUG_ON()`.
- Both checks vanish without `CONFIG_DEBUG_VM`; the folio is returned either
  way and no reference is taken.
- Split race: `softleaf_migration_sync()` issues `smp_rmb()` before the lock
  test, pairing with the write barrier in `__split_folio_to_order()`, so a new
  tail folio is not seen unlocked; the barrier is not under
  `CONFIG_DEBUG_VM`.
- `softleaf_to_page()` and `pmd_to_softleaf_folio()`: make the same lock
  check.
- Lifetime: the folio is valid only while the PTL covering the entry is held;
  the migrator holds a reference and must take that PTL to remove the entry.
- `softleaf_entry_wait_on_locked()` in `mm/filemap.c`: the waiter; it queues
  on the folio waitqueue under the PTL, drops the PTL, and takes no folio
  reference. There is no migration_entry_wait_on_locked() here.
- `softleaf_entry_wait_on_locked()` also serves device-private entries, from
  `do_swap_page()`.

**PFN in the offset field**

- `softleaf_to_pfn()`: always returns `swp_offset(entry) & SWP_PFN_MASK`, on
  every architecture; there is no swp_offset_pfn() here.
- `SWP_PFN_BITS`: `MAX_PHYSMEM_BITS - PAGE_SHIFT` when `MAX_PHYSMEM_BITS` is
  defined; the `min_t()` against `SWP_TYPE_SHIFT` applies only when it is not.
- Migration entry offset: PFN plus `SWP_MIG_YOUNG` and `SWP_MIG_DIRTY`
  directly above it; no other PFN-carrying kind uses bits above the PFN.
- Device-private entry offset: an ordinary `page_to_pfn()` value.
- Marker offset: read with `softleaf_to_marker()`, which masks with
  `PTE_MARKER_MASK`.
- **Unsafe usage**: taking `swp_offset()` of a migration entry as the PFN.
  - Safe: `softleaf_to_pfn()`, as `check_pte()` does; `SWP_PFN_MASK` in
    `include/linux/swapops.h` defines which bits are PFN.
  - Safe: passing the whole `swp_offset(entry)` to
    `make_readable_migration_entry()` when rewriting an entry, as
    `copy_nonpresent_pte()` does; that keeps the A/D bits on purpose.

**Bits in a swap-format entry**

- Without `CONFIG_HAVE_ARCH_USERFAULTFD_WP`: the `pte_` and `pmd_` uffd
  accessors are stubs in `include/asm-generic/pgtable_uffd.h`; tests return
  0, setters return the entry unchanged.
- PMD exclusive bit: none; PMDs have only soft-dirty and uffd.
- **Potentially unsafe usage**: a swap-bit accessor on a present entry, or a
  present-entry accessor on a swap-format entry.
  - Unsafe: when the bit read is acted on or copied into a new entry; on
    x86-64 the swap bits alias present-entry bits (`_PAGE_SWP_SOFT_DIRTY` is
    `_PAGE_RW`, `_PAGE_SWP_UFFD` is `_PAGE_USER`, `_PAGE_SWP_EXCLUSIVE` is
    `_PAGE_PWT`).
  - Safe: branch on `pte_present()` first, as `swp_pte_prepare()` in
    `mm/rmap.c` does.
  - Safe: `pte_swp_uffd_any()` in `include/linux/userfaultfd_k.h`, which
    returns false for a present PTE before it looks at the bit.
  - Safe: clearing the swap bits of a possibly-present PTE only to compare
    it with a swap-format value, as `pte_same_as_swp()` does for
    `unuse_pte()` in `mm/swapfile.c`; the other side is
    `swp_entry_to_pte(entry)`, which a present PTE never equals.

| Helper | Ignores the soft-dirty, uffd and exclusive bits |
|---|---|
| `softleaf_from_pte()`, then compare `.val` | yes |
| `pte_same_as_swp()` (static in `mm/swapfile.c`) | yes, on its first argument |
| `pte_same()` | no |
| `swap_pte_batch()` in `mm/internal.h` | no; batch ends where a bit differs |

- `pte_move_swp_offset()` in `mm/internal.h`: re-applies all three bits to
  the entry it builds.

**A/D bits in migration entries**

- `migration_entry_supports_ad()`: returns `swap_migration_ad_supported`,
  which `swapfile_init()` sets when
  `swapfile_maximum_size >= (1UL << SWP_MIG_TOTAL_BITS)`; it has nothing to do
  with THP migration support.
- `CONFIG_SWAP` off: `migration_entry_supports_ad()` returns false, so no
  migration entry carries A/D.
- Test helpers: `softleaf_is_migration_young()` and
  `softleaf_is_migration_dirty()` in `include/linux/leafops.h`; there is no
  is_migration_entry_young() or is_migration_entry_dirty() here.
- Unsupported case: the makers return the entry unchanged and the tests
  return false, so the PTE comes back old and clean; the dirtiness is kept on
  the folio, which `try_to_migrate_one()` marked with `folio_mark_dirty()`
  when it replaced a dirty PTE.
- Source entry not present: `try_to_migrate_one()`,
  `set_pmd_migration_entry()` and `migrate_vma_collect_pmd()` set the bits
  only when the replaced entry was present, so a device-private entry turned
  into a migration entry records neither.
- Dirty on removal: `remove_migration_pte()` and `remove_migration_pmd()`
  call the mkdirty helper only when `folio_test_dirty(folio)` and
  `softleaf_is_migration_dirty(entry)` both hold.

**Restoring software bits**

- uffd carry: `pte_swp_uffd()` to `pte_mkuffd()`, `pmd_swp_uffd()` to
  `pmd_mkuffd()`; there is no pte_swp_uffd_wp() or pte_mkuffd_wp() here.
- `pte_mkuffd()`: also write-protects on x86, arm64 and riscv.
- RWP restore: when the old entry has the swap uffd bit and
  `userfaultfd_rwp(vma)`, the new entry gets `pte_modify(pte, PAGE_NONE)`
  (`pmd_modify()` for a PMD) after the uffd bit is set, so the first access
  still faults.
- `do_swap_page()` on an RWP restore: also skips `pte_mkwrite()` and skips the
  `do_wp_page()` call for a write fault.
- Sites that carry soft-dirty and uffd and do the RWP restore:
  `do_swap_page()` and `restore_exclusive_pte()` in `mm/memory.c`,
  `remove_migration_pte()` and `try_to_map_unused_to_zeropage()` in
  `mm/migrate.c`, `unuse_pte()` in `mm/swapfile.c`, `remove_migration_pmd()`
  in `mm/huge_memory.c`.
- `migrate_vma_insert_page()`: not such a site; it bails out on any
  non-present, non-empty PTE.
- `remove_migration_pte()`: sets uffd only when the entry is not a write
  entry (`else if`); `remove_migration_pmd()` tests write and uffd
  independently.

**Rewriting a non-present entry**

- `change_softleaf_pte()`: exists, static in `mm/mprotect.c`, called for
  every non-present, non-empty PTE.
- Child uffd bit at fork: cleared unless `userfaultfd_protected(dst_vma)`,
  that is WP or RWP; same test in `copy_huge_non_present_pmd()`.

| Entry | Fork, `copy_nonpresent_pte()` | Protection change, `change_softleaf_pte()` |
|---|---|---|
| swap | exclusive cleared in parent and child, with no COW test; soft-dirty kept | unchanged |
| migration write | to read if `vma_is_cow_mapping(dst_vma)`; soft-dirty, uffd, A/D kept | to read-exclusive (anon) or read; soft-dirty and A/D kept, uffd not copied |
| migration read-exclusive | same as write | unchanged |
| device-private write | to read if `vma_is_cow_mapping(dst_vma)`; uffd kept, soft-dirty dropped | to read; uffd kept, soft-dirty dropped |
| device-private read, migration read, hwpoison | copied as is | unchanged |
| device-exclusive | restored to a present PTE by `try_restore_exclusive_pte()`, then copied as present | unchanged |
| poison or guard marker | `copy_pte_marker()` | returns before any uffd change |
| uffd-wp marker | `copy_pte_marker()` | cleared on a resolve flag, else untouched |

- uffd flags on protection change: `MM_CP_UFFD_WP` or `MM_CP_UFFD_RWP` sets
  `pte_swp_mkuffd()`; `MM_CP_UFFD_WP_RESOLVE` or `MM_CP_UFFD_RWP_RESOLVE`
  clears it; applied after the per-kind rewrite to every row except markers.
- PMD fork, `copy_huge_non_present_pmd()`: rewrites migration write and
  read-exclusive to read with no `vma_is_cow_mapping()` test; the
  device-private rewrite keeps both soft-dirty and uffd.
- PMD protection change, `change_non_present_huge_pmd()`: same bit rules as
  the PTE column, so device-private drops soft-dirty there but not at PMD
  fork.
- PMD paths run only when `thp_migration_supported()` and
  `pmd_is_valid_softleaf()`.

**Present-only page accessors**

- pte_folio(): not in this tree.
- `pmd_folio()`: a macro in `include/linux/pgtable.h`,
  `page_folio(pmd_page(pmd))`; it makes no check of its own.
- **Potentially unsafe usage**: `pmd_folio()` on a PMD once
  `pmd_trans_huge_lock()` has returned the lock.
  - Unsafe: when nothing tests presence afterwards; `pmd_is_huge()` in
    `include/linux/huge_mm.h` is true for every non-empty non-present PMD, so
    the lock is also returned for migration and device-private entries.
  - Safe: test `pmd_present()` under the lock first, as
    `madvise_free_huge_pmd()` in `mm/huge_memory.c` does.
- `pmd_to_softleaf_folio()`: in `include/linux/leafops.h`; returns NULL after
  `VM_WARN_ON_ONCE()` unless the entry is migration or device-private, so the
  caller must handle NULL.
- `pmd_to_softleaf_folio()` without `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`: always
  NULL.
- `pmd_to_softleaf_folio()` callers: only `normal_or_softleaf_folio_pmd()` in
  `mm/huge_memory.c`, for `zap_huge_pmd()`; other PMD code, for example
  `change_non_present_huge_pmd()`, uses
  `softleaf_to_folio(softleaf_from_pmd(pmd))`.

## Mapping and locking a table

**Page table descriptor**

- Destructor: there is no pagetable_pte_dtor() or pagetable_pmd_dtor() here;
  `pagetable_dtor()` in `include/linux/mm.h` serves every level, and
  `pagetable_dtor_free()` is that plus `pagetable_free()`.
- `init_mm`: `pagetable_pte_ctor()` and `pagetable_pmd_ctor()` skip the lock
  init when `mm == &init_mm`, so for a table constructed for `init_mm` they
  cannot fail.
- Skipped `pagetable_dtor()`: no bad-page report; `free_pages_prepare()` in
  `mm/page_alloc.c` resets a leftover page type silently.
- Skipped `pagetable_dtor()`, what stays wrong: `NR_PAGETABLE` is never
  subtracted, and under `CONFIG_SPLIT_PTE_PTLOCKS` with `ALLOC_SPLIT_PTLOCKS`
  the lock from `ptlock_alloc()` leaks.
- Deferred frees: the dtor runs inside the callback, not before it is queued,
  in `pte_free_now()` in `mm/pgtable-generic.c` and, under
  `CONFIG_MMU_GATHER_TABLE_FREE`, in `__tlb_remove_table()` in
  `include/asm-generic/tlb.h`.
- Without `CONFIG_MMU_GATHER_TABLE_FREE`: `tlb_remove_table()` calls
  `pagetable_dtor()` before it queues the page with `tlb_remove_page()`.
- `pagetable_free()` versus `__free_pages()`: `pagetable_free()` hands a table
  marked with `ptdesc_set_kernel()` to `pagetable_free_kernel()`; a direct
  `__free_pages()` skips that.
- `pagetable_free_kernel()` under `CONFIG_ASYNC_KERNEL_PGTABLE_FREE`: frees
  from a workqueue, after `iommu_sva_invalidate_kva_range()`; see
  `mm/pgtable-generic.c`.

**Page table locks**

- Configuration names: there is no USE_SPLIT_PTE_PTLOCKS or
  USE_SPLIT_PMD_PTLOCKS macro; code tests `CONFIG_SPLIT_PTE_PTLOCKS` and
  `CONFIG_SPLIT_PMD_PTLOCKS` (`mm/Kconfig`).
- `Documentation/mm/process_addrs.rst`: still writes USE_SPLIT_PMD_PTLOCKS;
  read it as `CONFIG_SPLIT_PMD_PTLOCKS`.
- `pud_lockptr()`: returns `&mm->page_table_lock` unconditionally; there is
  no split PUD lock.
- Two levels, example: the PMD-then-PTE pattern is in
  `try_collapse_pte_mapped_thp()` and `retract_page_tables()`;
  `collapse_pte_mapped_thp()` is only a wrapper.
- PTE lock already held, PMD lock wanted: only `spin_trylock()` on the PMD
  lock, as `zap_empty_pte_table()` in `mm/memory.c` does.
- When that trylock fails: drop the PTE lock and retake both in order, PMD
  first, then re-scan the table, as `zap_pte_table_if_empty()` does.

**Argument to the lock lookup**

- What is read: with `CONFIG_SPLIT_PTE_PTLOCKS`, only the value `*pmd`; the
  address of the entry is not used, so a pointer to a stack copy is valid.
- Without `CONFIG_SPLIT_PTE_PTLOCKS`: the argument is ignored and
  `&mm->page_table_lock` is returned, so a wrong argument shows no symptom.
- **Potentially unsafe usage**: `pte_lockptr(mm, pmd)` on the live PMD entry.
  - Unsafe: when nothing keeps the entry unchanged between the test that it
    points to a PTE table and the call; `pmd_page()` of a none, huge or
    non-present entry yields a lock in an unrelated page.
  - Safe: on a stack copy read once and validated, as `__pte_offset_map()`
    with `pte_offset_map_lock()` do in `mm/pgtable-generic.c`.
  - Safe: on the live entry while holding `pmd_lock()` and after validating
    under it, as `retract_page_tables()` does with `check_pmd_state()`;
    writers of the entry such as `pmd_install()` take that lock.
- **Unsafe usage**: `pte_lockptr()` on a table constructed for `init_mm`;
  `pagetable_pte_ctor()` never initialises that lock.
  - Safe: take no PTE lock for `init_mm`, as `apply_to_pte_range()` in
    `mm/memory.c` does with `pte_offset_kernel()`.
- `pmd_lockptr()` is the opposite: with `CONFIG_SPLIT_PMD_PTLOCKS`,
  `pmd_pgtable_page()` masks the address of the entry, so it needs the
  pointer into the live PMD table, never a copy.
- Call sites: four in the tree; other code gets the lock from
  `pte_offset_map_lock()`, `pte_offset_map_ro_nolock()` or
  `pte_offset_map_rw_nolock()`.

**Mapping a PTE table**

- NULL cases: decided only in `__pte_offset_map()`: PMD none, not present,
  `pmd_trans_huge()`, or `pmd_bad()`; there is no devmap test in this tree.
- `pmd_same()` mismatch in `pte_offset_map_lock()`: not a NULL return; it
  unlocks, unmaps and retries, and returns NULL only if the re-read PMD
  fails the tests above.
- `pte_offset_map_ro_nolock()` and `pte_offset_map_rw_nolock()`: make no
  `pmd_same()` test at all.
- On NULL: the RCU read lock is already dropped and `*ptlp` is not written,
  so the caller must not call `pte_unmap()` or touch `ptl`.
- `*pmdvalp` on NULL: it is written, with the value that failed the test.
- **Potentially unsafe usage**: writing entries after
  `pte_offset_map_rw_nolock()` and `spin_lock(ptl)` with no
  `pmd_same()` recheck.
  - Unsafe: when the entry the caller expects is none, or it compares no
    entry; a detached table is empty, so the check passes on it. The mmap
    write lock alone does not help: `retract_page_tables()` detaches under
    `i_mmap_rwsem` held for read.
  - Safe: `pmd_same(pmdval, pmdp_get_lockless(pmd))` under the lock, as
    `map_pte()` in `mm/page_vma_mapped.c` does.
  - Safe: `pte_same()` against an entry read earlier that is not none, as
    `handle_pte_fault()` does; `move_pages_ptes()` in `mm/userfaultfd.c`
    adds `pmd_same()` for its none destination for this reason.
  - Safe: `pmd_lock()` held from before the map until after the write, as
    `zap_pte_table_if_empty()` in `mm/memory.c` does.

**Between map and unmap**

- RCU guarantee, precondition: it holds only while the caller keeps the VMA
  attached and the mm in use; see the last paragraph of the comment above
  `pte_offset_map_lock()`.
- `free_pgtables()`: takes no page table lock and frees through
  `pte_free_tlb()`, which is deferred by RCU only under
  `CONFIG_MMU_GATHER_RCU_TABLE_FREE`.
- Immediate free, for example: `arch/arc/include/asm/pgalloc.h` defines
  `__pte_free_tlb()` as `pte_free()`.
- Paths that do wait for a grace period: `pte_free_defer()` and the
  `CONFIG_PT_RECLAIM` free in `zap_pte_range()`; that option depends on
  `MMU_GATHER_RCU_TABLE_FREE`.

**Pointer given to unmap**

- `CONFIG_HIGHPTE`: defined only in `arch/arm/Kconfig` here, with
  `depends on HIGHMEM && !PREEMPT_RT`; no other architecture has it.
- Everywhere else `pte_unmap()` is only `rcu_read_unlock()`, so a wrong
  pointer or wrong release order shows no symptom outside such arm builds.
- Release order, where it is written down: the comment at the `out:` label of
  `move_pages_ptes()` in `mm/userfaultfd.c`.

**Huge PMD lock helper**

- Test used by `pmd_trans_huge_lock()`: `pmd_is_huge()` in
  `include/linux/huge_mm.h`; there is no is_swap_pmd() and no pmd_devmap()
  in this tree.
- `pmd_is_huge()` accepts: a present PMD with `pmd_trans_huge()`, and every
  PMD that is neither present nor none.
- Checked twice: `pmd_trans_huge_lock()` tests unlocked, then
  `__pmd_trans_huge_lock()` tests again under `pmd_lock()`.
- Non-present helpers: there is no is_pmd_migration_entry() or
  pmd_to_swp_entry(); use `pmd_is_migration_entry()`,
  `pmd_is_device_private_entry()` and `softleaf_from_pmd()` from
  `include/linux/leafops.h`.
- Non-present does not mean no folio: get it with `pmd_to_softleaf_folio()`,
  never `pmd_folio()`; a device-private folio still has rmap and a
  reference, see `zap_huge_pmd_folio()`.
- Present kinds: see `insert_pmd()` in `mm/huge_memory.c`; a raw PFN and the
  huge zero folio get `pmd_mkspecial()`, any other folio is refcounted and
  rmapped.
- `vm_normal_folio_pmd()`: returns NULL for the special kinds.
- Code that gets it right: `madvise_free_huge_pmd()` and
  `madvise_cold_or_pageout_pte_range()` test `is_huge_zero_pmd()`, then
  `pmd_present()`, then call `pmd_folio()`.
- `zap_huge_pmd()` and `change_huge_pmd()`: also right, but they call
  `__pmd_trans_huge_lock()` directly.

**Locks for each operation**

- Freeing, mmap lock mode: the write lock is not always held;
  `vms_complete_munmap_vmas()` in `mm/vma.c` downgrades to read first when
  `vms->unlock`, then frees.
- Why that is safe: `vms_gather_munmap_vmas()` already ran
  `vma_start_write()` and `vma_mark_detached()` on each VMA under the write
  lock.
- `free_pgtables()` and the VMA lock: calls `vma_start_write()` only when
  `unmap->mm_wr_locked` is set.
- `free_pgtables()` and rmap: it does not hold the rmap locks while freeing;
  it removes each VMA from rmap with `unlink_anon_vmas()` and the
  `unlink_file_vma_batch_add()` batch, then calls `free_pgd_range()`.
- Rmap lock only, installing: not allowed into a previously empty entry.
- Why: `unmap_region()` runs `unmap_vmas()` and then `free_pgtables()`, and
  the VMA stays reachable through rmap until inside the latter; an entry
  installed in that window is freed with the table.
- Rmap lock only, freeing: `retract_page_tables()` detaches and frees an
  empty PTE table under `i_mmap_lock_read()`, not the write lock, plus the
  PMD and PTE locks, through `pte_free_defer()`.

**Fault handler lock order**

- `vmf_can_call_fault()`: the test is `vma->vm_ops->map_pages` non-NULL; only
  then may `fault`, `page_mkwrite` or `pfn_mkwrite` run with
  `FAULT_FLAG_VMA_LOCK` set.
- When the test fails: it calls `vma_end_read()` and returns
  `VM_FAULT_RETRY`.
- Handlers gated by it: `fault`, `page_mkwrite` and `pfn_mkwrite`; see
  `wp_page_shared()` and `wp_pfn_shared()` in `mm/memory.c`.
- `huge_fault`: not gated; `create_huge_pmd()` calls it with no
  `vmf_can_call_fault()` test.
- `do_shared_fault()`: tests once, before `fault`; `page_mkwrite` then runs
  under the same lock.
- A `vm_ops` that adds `map_pages` therefore declares that its `fault`,
  `page_mkwrite` and `pfn_mkwrite` need no mmap lock.

**User faults during buffered writes**

- No prefault up front: `generic_perform_write()` in `mm/filemap.c` goes
  straight to `write_begin` and `copy_folio_from_iter_atomic()`.
- Fault-in: the only `fault_in_iov_iter_readable()` call is after
  `write_end` returned 0 with `copied == 0`, when the folio is unlocked
  again.
- -EFAULT: set by `generic_perform_write()` itself only when that call
  returns `bytes`, meaning nothing could be faulted in.
- `write_end` returned 0: `chunk` is halved if above `PAGE_SIZE`; with
  `copied` non-zero the pass is retried with `bytes = copied`. There is no
  cap to a single iovec segment.
- `iomap_write_iter()` in `fs/iomap/buffered-io.c` differs: it calls
  `fault_in_iov_iter_readable()` before `iomap_write_begin()` on every pass
  and has no fault-in after a failed copy.

## The callback walker

**Walker callbacks**

- `pud_entry`, `pmd_entry`: called for every entry that is not `pud_none()` /
  `pmd_none()`, so also for leaf entries and for non-present ones (migration,
  device-private).
- `pte_hole` at PUD and PMD level: called for none entries only; a
  non-present entry is not a hole.
- `pgd_entry`, `p4d_entry`: the test is `pgd_none_or_clear_bad()` /
  `p4d_none_or_clear_bad()`; a bad entry is cleared and handled as a hole.
- None PMD in a walk without `install_pte`: gets `pte_hole` if set, and
  `pmd_entry` is not called for it.
- `depth`: takes only -1, 0, 1, 2, 3. There is no value for the PTE level;
  none PTEs go to `pte_entry`, or to `install_pte` when that is set.
- `depth` -1: a gap before or after a VMA, a `VM_PFNMAP` VMA skipped by the
  default test, and a hugetlb range where `hugetlb_walk()` returns NULL.
- `real_depth()` in `mm/pagewalk.c`: a hole found at a folded level is
  reported at the nearest level above that is not folded, for example 0 from
  `walk_p4d_range()` when `PTRS_PER_P4D == 1`.
- Huge PMD that `pmd_entry` already handled: the walker cannot tell; in a VMA
  walk with `pte_entry` set it still splits and descends unless the callback
  set `ACTION_CONTINUE`.
- After the split the walker goes straight to `walk_pte_range()`; it retries
  the PMD only if the PTE table cannot be mapped.
- `walk_pmd_range()` re-reads the PUD before it touches any PMD: if the PUD is
  not present or is a leaf it sets `ACTION_AGAIN` and returns 0.
- `walk_pud_range()` then retries that PUD, so `pud_entry` can run more than
  once for one PUD.
- `post_vma`: runs whenever `pre_vma` returned 0, including after a walk that
  returned non-zero; see `__walk_page_range()`.
- `pre_vma` and `post_vma` also run for a hugetlb VMA when no `hugetlb_entry`
  is set.

**Walks that install entries**

- Entry points that accept `install_pte`: `walk_page_range_mm_unsafe()` and
  `walk_page_range_vma_unsafe()`, defined in `mm/pagewalk.c` and declared in
  `mm/internal.h`.
- There is no walk_page_range_mm() and no check_ops_valid() here; the check is
  `check_ops_safe()`.
- Every entry point declared in `include/linux/pagewalk.h` that takes a
  `struct mm_walk_ops`, and `walk_page_range_debug()`, reaches
  `check_ops_safe()` and returns `-EINVAL` when `install_pte` is set. That
  includes `walk_page_range()` and `walk_page_range_vma()`.
- hugetlb VMA with `install_pte`: `__walk_page_range()` returns `-EINVAL`
  before `pre_vma` runs.
- None entry at each level: `__p4d_alloc()`, `__pud_alloc()`, `__pmd_alloc()`
  or `__pte_alloc()` runs in place of `pte_hole`; a non-zero return ends the
  walk and is returned.
- After the allocation the entry callback of that level runs on the new entry,
  so `pud_entry` and `pmd_entry` see entries they would not see in a plain
  walk.
- `install_pte` without `pte_entry`: a present `pmd_trans_huge()` PMD is
  skipped, not split, and nothing is installed under it; a present
  `pud_trans_huge()` PUD likewise, when `pmd_entry` is unset too.
- `install_pte` with `pte_entry`: huge entries are split as in any VMA walk.
- **Unsafe usage**: supplying `install_pte` without `pte_entry`.
  - Unsafe: `walk_pte_range_inner()` calls `ops->pte_entry` with no NULL test
    for every PTE that is not `pte_none()`.
  - Safe: supply both, as `madvise_guard_install()` in `mm/madvise.c` does.

**Walker entry points**

- There is no walk_page_range_novma() and no walk_page_range_mm() here. The
  entry points besides `walk_page_range()`, `walk_page_range_vma()`,
  `walk_page_vma()` and `walk_page_mapping()` are:

| Entry point | Scope | Asserted on the caller | `test_walk` |
|---|---|---|---|
| `walk_page_range_mm_unsafe()` | as `walk_page_range()` | as `walk_page_range()` | called |
| `walk_page_range_vma_unsafe()` | as `walk_page_range_vma()` | as `walk_page_range_vma()` | not called |
| `walk_kernel_page_table_range()` | `init_mm`, or `pgd` if given; no VMAs | `mmap_assert_locked(&init_mm)` | not called |
| `walk_kernel_page_table_range_lockless()` | same | nothing | not called |
| `walk_page_range_debug()` | any `mm`, or `pgd` if given; no VMAs | `mmap_assert_write_locked()` on `mm` and on `init_mm` | not called |

- `walk_page_range_debug()`: does not forward to
  `walk_kernel_page_table_range()`; it calls `walk_pgd_range()` itself, for
  `init_mm` too.
- `walk_kernel_page_table_range_lockless()`: takes and asserts no lock, so
  excluding every concurrent change to the range is left to the caller.
- No-VMA walks: take no PTE lock, split no huge entry, and leave `walk->vma`
  NULL; leaf and non-present PUDs and PMDs reach `pud_entry` and `pmd_entry`
  and are then skipped.
- `walk_page_mapping()`: iterates with `mapping_rmap_tree_foreach()`; there is
  no vma_interval_tree_foreach() in this tree.
- `walk_page_mapping()`: passes the whole VMA, `vm_start` to `vm_end`, to
  `test_walk`, not the clipped range it then walks.

**Walker locking**

| Value | mmap lock | Each VMA |
|---|---|---|
| `PGWALK_VMA_RDLOCK_VERIFY` | no assertion | `vma_assert_locked()` |

- `vma_assert_locked()`: passes for a VMA read lock and for a VMA write lock.
- `PGWALK_VMA_RDLOCK_VERIFY` drops the mmap lock requirement only for
  `walk_page_vma()`, `walk_page_range_vma()` and
  `walk_page_range_vma_unsafe()`.
- `walk_page_range()` and `walk_page_range_mm_unsafe()`: call `find_vma()`,
  which does `mmap_assert_locked()` itself, whatever `walk_lock` says.
- Without `CONFIG_PER_VMA_LOCK`: `process_vma_walk_lock()` is empty, so
  `PGWALK_WRLOCK` and `PGWALK_WRLOCK_VERIFY` only assert the mmap write lock,
  and `PGWALK_VMA_RDLOCK_VERIFY` asserts nothing.
- `PGWALK_WRLOCK`: `vma_start_write()` runs before `test_walk`, so a VMA that
  `test_walk` skips is write-locked too.
- `walk_page_mapping()`, `walk_kernel_page_table_range()`,
  `walk_kernel_page_table_range_lockless()` and `walk_page_range_debug()`: do
  not call `process_mm_walk_lock()` or `process_vma_walk_lock()`; `walk_lock`
  is ignored there.

**PMD callbacks and huge entries**

- Non-present PMD that is not none: it is a huge software leaf entry
  (migration, device-private).
- `pmd_trans_huge_lock()`: tests `pmd_is_huge()` in
  `include/linux/huge_mm.h`, which is true for a present `pmd_trans_huge()`
  PMD and for any non-present non-none PMD.
- Under that lock the callback tests `pmd_present()` before `pmd_folio()`, as
  `mlock_pte_range()` in `mm/mlock.c` does.
- Failed mapping of the PTE table: the callback either sets `ACTION_AGAIN` and
  returns 0, as `smaps_pte_range()` does, or returns 0 and skips the range, as
  `damon_mkold_pmd_entry()` in `mm/damon/vaddr.c` does.
- `split_huge_pmd()` in the walker: tests `pmd_is_huge()`, so it splits
  non-present huge entries as well as present ones.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `split_huge_pmd()` is an empty macro
  and `pmd_trans_huge_lock()` returns NULL.
- No-VMA walk: `walk->vma` is NULL and `__pmd_trans_huge_lock()` dereferences
  it, so the callback tests `pmd_leaf()` itself, as `vmemmap_pmd_entry()` in
  `mm/hugetlb_vmemmap.c` does.

**Return values and skipped VMAs**

- `walk_page_range()` without `test_walk`: `walk_page_test()` skips every
  `VM_PFNMAP` VMA; it is never walked, with or without `pte_hole`.
- Skipped `VM_PFNMAP` VMA in `walk_page_range()`: `pte_hole`, if set, is
  called once for the part of the VMA inside the range, with depth -1.
- `pte_hole` return on that path: negative aborts the walk; zero and positive
  both mean skip, so a positive value never reaches the caller there.
- Supplied `test_walk`: replaces the `VM_PFNMAP` check, so it has to reject
  `VM_PFNMAP` itself if it wants that, as `clear_refs_test_walk()` in
  `fs/proc/task_mmu.c` does.
- **Unsafe usage**: a `test_walk` that returns a positive value to skip one
  VMA, in ops passed to `walk_page_mapping()`.
  - Unsafe: `walk_page_mapping()` ends its loop over VMAs on a positive
    `test_walk` return and returns 0; the remaining VMAs of the mapping are
    not walked.
  - Safe: the same return in ops passed to `walk_page_range()`;
    `walk_page_range_mm_unsafe()` skips that VMA and continues with the next,
    as for `clear_refs_test_walk()` in `fs/proc/task_mmu.c`.
- `walk_page_vma()`, `walk_page_range_vma()` and
  `walk_page_range_vma_unsafe()`: do not call `walk_page_test()`, so they walk
  a `VM_PFNMAP` VMA.
- hugetlb VMA with no `hugetlb_entry`: no page table of it is walked and the
  result for it is 0.

**Retrying from a callback**

- `walk_pte_range()` when the PTE table cannot be mapped: sets
  `walk->action = ACTION_AGAIN` and returns 0; it does not return `-EAGAIN`.
- `walk_pmd_range()` on `ACTION_AGAIN`: jumps back and re-reads the PMD.
- Retry with the PMD now none, in a walk without `install_pte`: the walker
  calls `pte_hole` if set and moves on; `pmd_entry` is not called again.
- Retry with the PMD not none: `pmd_entry` runs again, then
  `split_huge_pmd()`, then the mapping is tried again.
- Ops with both `pmd_entry` and `pte_entry`: `pmd_entry` can run more than
  once for one PMD because of the walker's own retry, so it must tolerate a
  repeat even if it never sets `ACTION_AGAIN`.
- **Potentially unsafe usage**: setting `ACTION_AGAIN` from `pmd_entry`.
  - Unsafe: when the PMD state that made the callback set it can still be
    there on the retry and the callback sets it again; `walk_pmd_range()` has
    no retry limit and loops with the caller's locks held.
  - Safe: straight after `pte_offset_map_lock()` returned NULL, in a callback
    that first took `pmd_is_huge()` entries through `pmd_trans_huge_lock()`,
    as `smaps_pte_range()` in `fs/proc/task_mmu.c` does.
  - Safe: `__pte_offset_map()` in `mm/pgtable-generic.c` defines the failing
    states: none, non-present, `pmd_trans_huge()`, or bad and then cleared. On
    the retry the walker takes a none PMD and the huge branch takes the rest.

## The reverse-map walker and GUP-fast

**Reverse-map walk state**

- `pvmw->pte` set on a non-hugetlb VMA: the caller is also inside the
  `rcu_read_lock()` taken by `__pte_offset_map()`; hugetlb `pvmw->pte` comes
  from `hugetlb_walk()` with no map and no RCU section.
- Lock coverage across calls: the next call keeps `pvmw->ptl` while it stays in
  the same PTE table; at a table boundary it unlocks, unmaps and sets
  `PVMW_PGTABLE_CROSSED` in `pvmw->flags`, so entries returned earlier are no
  longer locked.
- `PVMW_PGTABLE_CROSSED`: never cleared by the walker; `folio_referenced_one()`
  and `try_to_unmap_one()` test it before `mlock_vma_folio()`.
- `page_vma_mapped_walk_done()`: clears no field; `not_found()` has already
  called it on every false return that held `pvmw->ptl`, so a second call
  unlocks `pvmw->ptl` again.
- `page_vma_mapped_walk_restart()`: needs `pvmw->ptl` held and `pvmw->pmd` or
  `pvmw->pte` set, and warns otherwise.
- `page_vma_mapped_walk_restart()`: unlocks and sets `ptl`, `pmd`, `pte` to
  NULL; it does not call `pte_unmap()` and does not touch `pvmw->address`.
- **Unsafe usage**: `page_vma_mapped_walk_restart()` while `pvmw->pte` is
  mapped on a non-hugetlb VMA.
  - Unsafe: the pointer is set to NULL with no `pte_unmap()`, so the
    `rcu_read_lock()` of `__pte_offset_map()` is never dropped.
  - Safe: after a PMD-level return (`pvmw->pte` NULL), as `try_to_unmap_one()`
    does after `split_huge_pmd_locked()`.
- **Potentially unsafe usage**: changing `pvmw->pte` or `pvmw->address`
  between calls.
  - Unsafe: when the two no longer match, or the new position leaves the PTE
    table that `pvmw->ptl` locks; the next call resumes from these fields.
  - Safe: advancing both by the same count inside one table, as
    `folio_referenced_one()` does with a batch bounded by `pmd_addr_end()`;
    `page_vma_mapped_walk()` then steps both by one and tests the table
    boundary on `pvmw->address`.

**Entries the reverse-map walk returns**

- There is no is_migration_entry(), is_device_private_entry(),
  is_pmd_migration_entry() or swp_offset_pfn() here; `check_pte()` uses
  `softleaf_from_pte()`, `softleaf_is_migration()`,
  `softleaf_is_device_private()`, `softleaf_is_device_exclusive()` and
  `softleaf_to_pfn()` from `include/linux/leafops.h`.
- Device-exclusive PTE: a non-present entry (`SOFTLEAF_DEVICE_EXCLUSIVE`);
  returned without `PVMW_MIGRATION`, never with it.
- Device-private PTE: returned without `PVMW_MIGRATION`, never with it.
- Device-private PMD: returned with `pvmw->pte` NULL without
  `PVMW_MIGRATION`, after `check_pmd()` on `softleaf_to_pfn()`; with the flag
  the walk returns false.
- Migration PMD: the walker does not call `thp_migration_supported()`; the
  gate is `IS_ENABLED(CONFIG_TRANSPARENT_HUGEPAGE)` plus
  `pmd_is_migration_entry()`, which is false without
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`.
- PMD leaf of the wrong kind for the flag, or one that fails `check_pmd()`:
  `page_vma_mapped_walk()` returns false at once through `not_found()`; it
  does not `step_forward()` to the next PMD.
- Non-present PMD of any other kind with `PVMW_SYNC`:
  `sync_with_folio_pmd_zap()` runs only when `thp_vma_suitable_order()` holds
  and `pvmw->nr_pages >= HPAGE_PMD_NR`.

**Accessors in reverse-map callbacks**

- There is no is_writable_migration_entry(),
  is_readable_exclusive_migration_entry() or
  is_writable_device_private_entry() here; use
  `softleaf_is_migration_write()`, `softleaf_is_migration_read_exclusive()`
  and `softleaf_is_device_private_write()`.
- There is no ptep_clear_flush_young_notify() here;
  `clear_flush_young_ptes_notify()` in `mm/internal.h` takes a count of PTEs.
- `softleaf_from_pte()`: strips soft-dirty, uffd and exclusive bits with
  `pte_swp_clear_flags()`, so read them from the `pte_t` with
  `pte_swp_soft_dirty()` and `pte_swp_uffd()`, not from the `softleaf_t`.
- `pte_swp_exclusive()`: used by no rmap callback; `try_to_migrate_one()`
  takes exclusivity from `PageAnonExclusive()` on the subpage, and
  `remove_migration_pte()` from the entry type
  (`!softleaf_is_migration_read(entry)` on an anon folio).
- **Potentially unsafe usage**: `pte_pfn()`, `pte_write()`, `pte_young()`,
  `pte_dirty()`, `pte_soft_dirty()` or `pte_uffd()` on the returned entry of a
  walk without `PVMW_MIGRATION`.
  - Unsafe: with no `pte_present()` test, when the folio can be mapped by a
    device-private or device-exclusive entry; `make_device_exclusive()`
    accepts any anonymous non-hugetlb folio.
  - Safe: after a `pte_present()` test, with the softleaf helpers on the
    other branch, as `try_to_migrate_one()` and `try_to_unmap_one()` do;
    `check_pte()` defines which non-present kinds are returned.
  - Safe: skipping the entry when `!pte_present()`, as
    `page_vma_mkclean_one()` and `write_protect_page()` in `mm/ksm.c` do.
- PMD level, present and non-present: `set_pmd_migration_entry()` in
  `mm/huge_memory.c`, called from `try_to_migrate_one()`, and
  `damon_pmdp_mkold()` in `mm/damon/ops-common.c`.

**Lockless walk by GUP-fast**

- Recheck after `try_grab_folio_fast()`: compares against
  `pmdp_get_lockless(pmdp)` and `ptep_get_lockless(ptep)`, not plain reads;
  under `CONFIG_GUP_GET_PXX_LOW_HIGH` these read the entry in two halves (the
  PMD only with more than two levels).
- `page_folio(page) != folio` test: in `try_get_folio()`, which drops the
  reference and retries; `gup_fast_pte_range()` has no such test of its own.
- IRQs off rather than `rcu_read_lock()`: `tlb_remove_table_sync_one()` is
  `smp_call_function()` with wait, not an RCU grace period, so only a walker
  with IRQs disabled holds it off.
- khugepaged: only `collapse_huge_page()` calls `tlb_remove_table_sync_one()`
  by name after `pmdp_collapse_flush()`; `try_collapse_pte_mapped_thp()` and
  `retract_page_tables()` call `pmdp_get_lockless_sync()` and then
  `pte_free_defer()`.
- `pmdp_get_lockless_sync()`: `tlb_remove_table_sync_one()` only under
  `CONFIG_GUP_GET_PXX_LOW_HIGH` with more than two levels; empty otherwise
  (`include/linux/pgtable.h`).
- A table detached for reuse has the same requirement as one that is freed:
  `tlb_flush_unshared_tables()` calls `tlb_remove_table_sync_one()` when
  `tlb->fully_unshared_tables` is set, before a hugetlb PMD table can be
  reused.

## PTE batching

**Batch flags and default comparison**

- `fpb_t` in `mm/internal.h`: exactly five flags, `FPB_RESPECT_DIRTY`,
  `FPB_RESPECT_SOFT_DIRTY`, `FPB_RESPECT_WRITE`, `FPB_MERGE_WRITE` and
  `FPB_MERGE_YOUNG_DIRTY`.
- Young bit: ignored under every flag combination;
  `__pte_batch_clear_ignored()` ends with an unconditional `pte_mkold()`.
- `FPB_MERGE_WRITE` and `FPB_MERGE_YOUNG_DIRTY`: do not change what is
  compared; `__pte_batch_clear_ignored()` tests only `FPB_RESPECT_DIRTY`,
  `FPB_RESPECT_SOFT_DIRTY` and `FPB_RESPECT_WRITE`.
- `FPB_MERGE_YOUNG_DIRTY` with `FPB_RESPECT_DIRTY`: dirty must still match
  across the batch.
- Small folio: `folio_pte_batch_flags()` has no early return for it, only
  `VM_WARN_ON_FOLIO()`; callers make sure the folio is large first, as
  `mprotect_folio_pte_batch()` does with `folio_test_large()`.
- `ptentp` pointing into a page table: caught only by a `VM_WARN_ON()`, which
  is compiled out without `CONFIG_DEBUG_VM`; the merge flags write through
  `*ptentp`, so they would then modify the live entry.
- Userfaultfd bit (`pte_uffd()`): compared under every flag combination.

**Ranged PTE helpers**

- There is no clear_not_present_full_ptes() here; `clear_nonpresent_ptes()` in
  `include/linux/pgtable.h` does that, takes no `full` argument and loops over
  `pte_clear()`.
- `ptep_get_and_clear_full()` and `ptep_test_and_clear_young()`: single-PTE
  operations; the ranged forms are `get_and_clear_full_ptes()` and
  `test_and_clear_young_ptes()`.

| Helper | Bits that differ across the run | Requires of the run |
|---|---|---|
| `clear_full_ptes()`, `clear_ptes()` | all discarded; return `void` | present, one folio |
| `clear_flush_young_ptes()` | kept per entry; returns `bool`, true if any entry was young | present, one folio |
| `test_and_clear_young_ptes()` | kept per entry; returns `bool`, true if any entry was young; no TLB flush | present, one folio |
| `clear_young_dirty_ptes()` | kept per entry, apart from the bits the `cydp_t` flags clear | present, one folio |
| `modify_prot_start_ptes()` | the generic form clears each entry; an arch override may not, for example Xen PV leaves it present; returns the first with young and dirty ORed in | all bits but young and dirty identical |
| `modify_prot_commit_ptes()` | writes one value, PFN advanced per entry | entries that the start call was run on |
| `clear_nonpresent_ptes()` | all discarded | all not present; no folio relation |

- `modify_prot_start_ptes()`: the stricter requirement comes from the commit
  writing one value; `change_pte_range()` in `mm/mprotect.c` meets it by
  batching with `FPB_RESPECT_SOFT_DIRTY | FPB_RESPECT_WRITE`.
- `set_ptes()` with `nr` > 1: every entry must be not present before the call
  and present after it; `contpte_set_ptes()` in `arch/arm64/mm/contpte.c`
  relies on this and does not unfold or invalidate first.
- `set_ptes()` with `nr` == 1 (`set_pte_at()`): either state is allowed before
  and after.

**Writing a batch back**

- `folio_unmap_pte_batch()` in `mm/rmap.c`: passes
  `FPB_RESPECT_WRITE | FPB_RESPECT_SOFT_DIRTY`, not zero flags.
- `folio_unmap_pte_batch()`: returns 1 without batching for anon swapbacked
  folios, `TTU_HWPOISON`, small folios and `pte_unused()`; lazyfree and file
  folios are batched.
- `try_to_unmap_one()`: writes the run back with `set_ptes()` when
  `ttu_anon_folio()` fails; the value is the `get_and_clear_ptes()` result, so
  young and dirty spread over the run, while write and soft-dirty are uniform
  by the flags.
- `copy_present_ptes()` in `mm/memory.c`: passes `FPB_MERGE_WRITE`, plus
  `FPB_RESPECT_DIRTY` unless `VM_SHARED`, plus `FPB_RESPECT_SOFT_DIRTY` when
  `vma_soft_dirty_enabled()`; it never passes `FPB_RESPECT_WRITE`.
- `__copy_present_ptes()`, how each ignored bit is handled:
  - write, COW mapping: `wrprotect_ptes()` on the source run and
    `pte_wrprotect()` on the child value when the merged value is writable.
  - write, other mappings: the child run is written with the merged write bit.
  - dirty: uniform by flag in a private mapping; `pte_mkclean()` in a shared
    one.
  - young: `pte_mkold()` on the child value; the source keeps its own.
- `move_ptes()` in `mm/mremap.c`: batches through `mremap_folio_pte_batch()`,
  which returns 1 when `pte_batch_hint()` is 1, and otherwise passes
  `FPB_RESPECT_WRITE` for any large folio that `vm_normal_folio()` returns,
  anon or file.
- `move_ptes()`, ignored bits: young and dirty are ORed by
  `get_and_clear_ptes()`; `move_soft_dirty_pte()` sets soft-dirty on the value
  when `pgtable_supports_soft_dirty()`.
- No flags: `zap_present_ptes()` calls `folio_pte_batch()` and writes no
  present entry back; `zap_present_folio_ptes()` only clears, and may install
  `PTE_MARKER_UFFD_WP` markers from the userfaultfd bit, which is compared.
- Other callers of `folio_pte_batch()`: search for the name; each one only
  reads, clears, or uses a per-entry helper.
- **Unsafe usage**: writing one value over the run with `set_ptes()` or
  `modify_prot_commit_ptes()` after a batch that passed neither
  `FPB_RESPECT_WRITE` nor `FPB_MERGE_WRITE`.
  - Unsafe: the value carries the write bit of the first entry, so entries that
    were read-only become writable, or the reverse.
  - Safe: pass `FPB_RESPECT_WRITE`, as `mremap_folio_pte_batch()`,
    `folio_unmap_pte_batch()` and `change_pte_range()` do.
  - Safe: pass `FPB_MERGE_WRITE` and write-protect the whole run in a COW
    mapping, as `__copy_present_ptes()` does.
  - Safe: change entries only with a per-entry helper, as
    `madvise_free_pte_range()` does with `clear_young_dirty_ptes()`.

**Batch bounds**

- Return value: `min(nr, max_nr)` with `max_nr` already capped to the folio
  end, because `pte_batch_hint()` can step past `max_nr`.
- Folio end: capped by `folio_pte_batch_flags()` itself; the caller need not
  clamp to it.
- `max_nr` of 0: only a `VM_WARN_ON_FOLIO()` under `CONFIG_DEBUG_VM`; the
  function returns 0, so a loop that advances by the result does not advance.
- `max_nr` in `mm/memory.c`: computed in `copy_pte_range()` and
  `do_zap_pte_range()` as `(end - addr) / PAGE_SIZE`; `copy_present_ptes()`
  and `zap_present_ptes()` receive it as a parameter.
- `do_zap_pte_range()`: subtracts the leading none entries it skipped before
  it passes `max_nr` on.
- Run written into a second page table: `max_nr` must fit that table too;
  for `move_ptes()`, `get_extent()` in `mm/mremap.c` clamps the extent to the
  PMD of the old address and of the new one.

**Large folio over populated PTEs**

- `finish_fault()`, `nr_pages` > 1 and the range not empty under the PTL: sets
  `needs_fallback`, drops the PTL, jumps back to `fallback:` and maps only the
  faulting page.
- `finish_fault()` returns `VM_FAULT_NOPAGE` only when `vmf_pte_changed()` is
  true for the faulting entry itself, or `pte_offset_map_lock()` returns NULL.
- `finish_fault()` maps the whole folio for any mapping, not only shmem, when
  all of these hold:
  - `userfaultfd_armed()` is false;
  - the folio fits inside the VMA and inside one page table;
  - the mapping is shmem, or the folio does not extend past `i_size`
    (`file_end < folio_next_index(folio)` sets `needs_fallback`);
  - every entry of the range is none under the PTL.
- `pte_range_none()`: static in `mm/memory.c`; reads with
  `ptep_get_lockless()`, which is what allows the call under `pte_offset_map()`
  without the PTL.
- `alloc_anon_folio()`: `pte_offset_map()` returning NULL gives
  `ERR_PTR(-EAGAIN)`, and `do_anonymous_page()` then returns 0.
- `do_anonymous_page()`: rechecks `folio_nr_pages(folio)` entries of the folio
  actually allocated, which can be a lower order than the first order that
  passed the unlocked check.
- `do_anonymous_page()`: tests `userfaultfd_missing()` under the PTL, after
  the recheck, and drops the folio before `handle_userfault()`.
- **Unsafe usage**: `set_ptes()` with `nr` > 1 over a range whose emptiness was
  checked only by an unlocked `pte_range_none()`.
  - Unsafe: `set_ptes()` with `nr` > 1 needs every entry not present;
    `contpte_set_ptes()` in `arch/arm64/mm/contpte.c` relies on it and does
    not unfold or invalidate first.
  - Safe: retake the table with `pte_offset_map_lock()`, repeat
    `pte_range_none()` over the folio's aligned range, and on failure drop the
    folio and return 0, as `do_anonymous_page()` does.

## Zapping and freeing tables

**Zap functions**

- zap_page_range_single, zap_page_range_single_batched, zap_vma_ptes,
  unmap_page_range and unmap_single_vma are not in this tree. The functions
  are these, all in `mm/memory.c`:

| Function | Use | Caller must already have |
|---|---|---|
| `zap_vma_range()` | range within one VMA, NULL details | VMA kept alive by the caller, for example by the mmap lock or a VMA read lock; no lock is asserted. Not exported |
| `zap_vma_range_batched()` | same, caller's gather and details | gather started on `vma->vm_mm`; it does the notifier and `update_hiwater_rss()` itself. `unmap_mapping_range_tree()` calls it under `i_mmap_rwsem` only |
| `zap_special_vma_range()` | drivers; `EXPORT_SYMBOL_GPL` | nothing checked by caller: silently does nothing unless the range is inside the VMA and the VMA has `VM_PFNMAP` or `VM_MIXEDMAP` |
| `zap_vma_for_reaping()` | OOM reaper, whole VMA | mmap read lock; non-hugetlb VMA. Own gather, own non-blocking notifier |
| `unmap_vmas()` | munmap, exit; takes a `struct unmap_desc` (`mm/vma.h`) | gather started, mmap lock in either mode; it does not call `update_hiwater_rss()` (`unmap_region()` does before it, `exit_mmap()` does not) |
| `__zap_vma_range()` | static; reached by all of the above | gather, notifier started, and for hugetlb `hugetlb_zap_begin()` |

- `zap_vma_for_reaping()`: returns `-EBUSY` when the notifier would block;
  `__oom_reap_task_mm()` picks the VMAs and calls it.
- `.reaping`: makes `__zap_vma_range()` skip `uprobe_munmap()`.
- `lru_add_drain()`: not called by any of these.
- `unmap_vmas()` in `exit_mmap()`: runs under `mmap_read_lock()`; the write
  lock is taken only afterwards, for `free_pgtables()`.
- `zap_vma_range_batched()` on a hugetlb VMA: takes the hugetlb VMA lock and
  `i_mmap_rwsem` for write through `hugetlb_zap_begin()`, so the caller must
  hold neither.
- `struct zap_details`: has `skip_cows`, not an `even_cows` member;
  `unmap_mapping_pages()` sets `skip_cows = !even_cows`. `unmap_vmas()` sets
  only `zap_flags`.

**The mmu_gather contract**

- Table pages, `CONFIG_MMU_GATHER_RCU_TABLE_FREE`: a batch is freed by
  `call_rcu()` after the flush. The gather never frees a table after an IPI
  sync.
- `CONFIG_MMU_GATHER_TABLE_FREE`: selected only by
  `MMU_GATHER_RCU_TABLE_FREE` (`arch/Kconfig`), so the non-RCU
  `tlb_remove_table_free()` in `mm/mmu_gather.c`, which frees directly with
  no wait, is built in no configuration.
- `tlb_table_invalidate()`: flushes before tables are freed only if
  `tlb_needs_table_invalidate()` is true.
- `tlb_remove_table()` with a full batch (`MAX_TABLE_BATCH`): flushes and
  hands the tables to `call_rcu()` at once, while pages stay batched until
  the next `tlb_flush_mmu()`.
- `tlb_finish_mmu()`: starts with
  `VM_WARN_ON_ONCE(tlb->fully_unshared_tables)`; a gather that unshared a
  hugetlb PMD table must have gone through `huge_pmd_unshare_flush()` first.
- `mm_tlb_flush_nested()` in `tlb_finish_mmu()`: also true while
  `wp_clean_pre_vma()` in `mm/mapping_dirty_helpers.c` has raised
  `mm->tlb_flush_pending`; that path uses no gather.

**Starting a gather**

- `tlb_gather_mmu_vma()` in `mm/mmu_gather.c`: `tlb_gather_mmu()` on
  `vma->vm_mm`, then `tlb_update_vma_flags()`, then for a hugetlb VMA
  `tlb_change_page_size()` to the hstate size.
- `tlb_gather_mmu_vma()`: records no range and does not call
  `flush_cache_range()`; its callers call `flush_cache_range()` themselves
  and need no `tlb_start_vma()`.
- `tlb_gather_mmu_vma()` callers: all are hugetlb paths that may unshare a
  PMD table, in `mm/hugetlb.c` and `mm/rmap.c`.
- After `huge_pmd_unshare()`: the caller must call
  `huge_pmd_unshare_flush()` while still holding `i_mmap_rwsem` for write
  (it asserts that), and before `tlb_finish_mmu()`.
- `tlb_gather_mmu_fullmm()`: used by `exit_mmap()` and by
  `free_ldt_pgtables()` in `arch/x86/kernel/ldt.c`; with `fullmm` the x86
  `tlb_flush()` ignores the tracked range.
- `fullmm`: makes `tlb_start_vma()`, `tlb_end_vma()` and `tlb_free_vmas()`
  return at once.
- `tlb_gather_mmu()` followed by `zap_vma_range_batched()`: notifier and
  `update_hiwater_rss()` are done for the caller; followed by
  `unmap_vmas()`: only the notifier is.

**Table freeing and lockless walkers**

- `tlb_remove_table()` batch allocation failure, `CONFIG_PT_RECLAIM`:
  `tlb_table_invalidate()`, then `call_rcu()` on `pt_rcu_head` of the
  `struct ptdesc`; does not sleep.
- `tlb_remove_table()` batch allocation failure, no `CONFIG_PT_RECLAIM`:
  `tlb_table_invalidate()`, then `tlb_remove_table_sync_rcu()`, then the
  table is freed at once. It does not call `tlb_remove_table_sync_one()`.
- `tlb_remove_table_sync_rcu()`: is `synchronize_rcu()`, so the
  allocation-failure path of `tlb_remove_table()` without
  `CONFIG_PT_RECLAIM` can sleep.
- `CONFIG_PT_RECLAIM`: not selectable; `def_bool y`, depends on
  `MMU_GATHER_RCU_TABLE_FREE && !HAVE_ARCH_TLB_REMOVE_TABLE` (`mm/Kconfig`).
- Without `CONFIG_MMU_GATHER_RCU_TABLE_FREE`:
  `tlb_remove_table_sync_one()` and `tlb_remove_table_sync_rcu()` are empty
  stubs in `include/asm-generic/tlb.h`, and `tlb_remove_table()` puts the
  table in the page batch, freed after the flush with no wait.

| Function | Waits for | Frees |
|---|---|---|
| `tlb_remove_table()` (through `pte_free_tlb()` and the like) | under `CONFIG_MMU_GATHER_RCU_TABLE_FREE`, an RCU grace period: `call_rcu()` for a batch | yes, later |
| `pte_free_defer()` | an RCU grace period, by `call_rcu()` | yes, later |
| `tlb_remove_table_sync_one()` | every other CPU to take an IPI, so to leave any IRQs-off walk | no |
| `tlb_remove_table_sync_rcu()` | an RCU grace period, blocking | no |

- `tlb_remove_table_sync_one()` called by name: only in
  `collapse_huge_page()` and `tlb_flush_unshared_tables()`, both for a table
  that is kept, not freed. `pmdp_get_lockless_sync()` is a macro for it
  under `CONFIG_GUP_GET_PXX_LOW_HIGH` with `CONFIG_PGTABLE_LEVELS` above 2,
  and that one runs before `pte_free_defer()`.
- Generic `pte_free_defer()` in `mm/pgtable-generic.c`: compiled only with
  `CONFIG_TRANSPARENT_HUGEPAGE`; powerpc, s390 and sparc define their own.

**Reclaiming empty PTE tables**

- There is no mm/pt_reclaim.c, try_get_and_clear_pmd or try_to_free_pte here;
  the zap path uses `zap_empty_pte_table()` and `zap_pte_table_if_empty()`
  in `mm/memory.c`.
- Zap path, when it reclaims: `pte_table_reclaim_possible()` needs
  `CONFIG_PT_RECLAIM`, `reclaim_pt`, and a range that covers the whole table
  (`end - start >= PMD_SIZE`); any entry left behind (`any_skipped`) cancels
  it.
- `reclaim_pt`: set only by `madvise_dontneed_single_vma()`, so the mm lock
  held is a VMA read lock or the mmap read lock.
- Zap path, free: `pte_free_tlb()` on the caller's gather, after the PTL is
  dropped.
- `retract_page_tables()`: takes no mmap lock and no VMA lock, not even by
  trylock; it holds `i_mmap_rwsem` for read, the pmd lock and the PTL.
- `file_backed_vma_is_retractable()`: skips a VMA with `anon_vma`, with
  `userfaultfd_protected()`, or with `VMA_MAYBE_GUARD_BIT`; it is called
  again under the PTL.
- `collapse_pte_mapped_thp()`: a wrapper; the work and
  `mmap_assert_locked()` are in `try_collapse_pte_mapped_thp()`, which
  returns early for `userfaultfd_protected()`.
- `try_collapse_pte_mapped_thp()`: takes the pmd lock before the PTL for
  step 2 only for a private VMA with `userfaultfd_armed()`; otherwise it
  holds the PTL alone for step 2, drops it, and at step 4 takes the pmd
  lock, then the PTL, with a `pmd_same()` recheck.

**Decisions across a lock drop**

- `zap_empty_pte_table()`: the no-rescan path, called with the PTL still
  held; `zap_pte_table_if_empty()`: the rescan path, called after the PTL
  was dropped. Both are in `mm/memory.c`.
- No rescan needs all of: `can_reclaim_pt`, `direct_reclaim`,
  `addr == end`, and the pmd lock obtained by `spin_trylock()` (or being the
  same lock as the PTL).
- `direct_reclaim`: cleared on a `need_resched()` or `force_break` exit and
  never set again, so a table zapped in more than one PTL hold always takes
  the rescan path.
- `any_skipped`: clears `can_reclaim_pt`, which disables both paths for that
  table.
- `zap_pte_table_if_empty()` lock order: `pmd_lock()`, then
  `pte_offset_map_rw_nolock()`, then the PTL with `SINGLE_DEPTH_NESTING`.
- `zap_pte_table_if_empty()`: does not call `pmd_same()`; the PMD is read
  with the pmd lock already held. It scans all `PTRS_PER_PTE` entries with
  `pte_none()` before `pmd_clear()`.
- After either path: `zap_pte_range()` calls `pte_free_tlb()` and
  `mm_dec_nr_ptes()` with no page table lock held.
- `retract_page_tables()`: an intended weaker recheck; it accepts a
  different table at the same PMD, because the folio lock held by
  `collapse_file()` blocks page faults on it, and repeats only
  `file_backed_vma_is_retractable()` under the PTL.

**Freeing tables at unmap**

- Signature: `free_pgtables(tlb, struct unmap_desc *)`; floor and ceiling
  are `pg_start` and `pg_end`, and `mm_wr_locked` is a member
  (`mm/vma.h`).
- hugetlb: no separate path; hugetlb_free_pgd_range is not in this tree and
  every VMA goes to `free_pgd_range()`.
- No TLB flush is required before the call: `unmap_region()` runs
  `unmap_vmas()` and `free_pgtables()` on one gather and finishes it once.
- `tlb_free_vmas()`: first call in `free_pgtables()`; if the gather is not
  `fullmm` and saw a `VM_PFNMAP` or `VM_MIXEDMAP` VMA it flushes the TLB
  before any VMA is unlinked from rmap, so `unmap_mapping_range()` cannot
  miss the VMA while its flush is pending.
- mmap lock: must be held in some mode; `unlink_anon_vmas()` asserts
  `mmap_assert_locked()`.
- Between detach and `free_pgtables()`: rmap walkers still reach the VMA
  through `anon_vma` or `i_mmap` and work on its tables under the PTL; on
  the unmap path the unlink happens inside `free_pgtables()`.
- After the unlink: `free_pgd_range()` clears and frees with no page table
  lock, so code that does not own the mm must not use `pte_offset_map()` and
  the like once the VMA is detached or `mm_users` is zero.
- `try_collapse_pte_mapped_thp()` does `vma_lookup()` first and
  `retract_page_tables()` tests `collapse_test_exit()` for that reason.
- Callers whose VMAs were not detached by munmap: `exit_mmap()` and
  `dup_mmap()` on failure, where the VMAs are still attached and
  `tear_down_vmas()` detaches them afterwards; and `__mmap_new_file_vma()`
  on a failed `mmap_file()`, where the VMA is not yet stored in the tree.
  All three hold the mmap write lock for `free_pgtables()`; the last two
  use `UNMAP_STATE()`.

**mmap write lock and tables**

- `collapse_huge_page()`: never frees the PTE table. At PMD order it
  deposits it with `pgtable_trans_huge_deposit()`; below PMD order it puts
  it back with `pmd_populate()`.
- `collapse_huge_page()` below PMD order: the PMD is none from
  `pmdp_collapse_flush()` until it is reinstalled; the mmap write lock,
  `vma_start_write()` and the anon_vma write lock are all held for that
  whole time.
- `collapse_huge_page()` at PMD order: drops the anon_vma lock once every
  page is isolated and locked.
- `zap_vma_range_batched()`: defined in `mm/memory.c`; asserts no lock, it
  checks `tlb->mm == vma->vm_mm`. zap_page_range_single_batched is not in
  this tree.
- madvise under a VMA read lock: `get_lock_mode()` in `mm/madvise.c`
  returns `MADVISE_VMA_READ_LOCK` for `MADV_DONTNEED`,
  `MADV_DONTNEED_LOCKED`, `MADV_FREE`, `MADV_GUARD_INSTALL` and
  `MADV_GUARD_REMOVE`.
- madvise fallback: `try_vma_read_lock()` takes the mmap read lock when
  `lock_vma_under_rcu()` fails or `is_vma_lock_sufficient()` is false: the
  range leaves the VMA, the mm is remote, the VMA has `userfaultfd_armed()`,
  or `MADV_GUARD_INSTALL` finds an anonymous VMA with no `anon_vma`.
- Other changers under a VMA read lock only: search for
  `lock_vma_under_rcu()`; besides faults, userfaultfd, TCP zerocopy and
  binder, `damon_va_walk_page_range()` in `mm/damon/vaddr.c` walks with
  `PGWALK_VMA_RDLOCK_VERIFY`.
- `MADV_DONTNEED` under a VMA read lock: sets `reclaim_pt`, so under
  `CONFIG_PT_RECLAIM` it can free a PTE table with no mmap lock held.

## TLB flushing

**Transitions that need a flush**

- `ptep_set_access_flags()` on x86 (`arch/x86/mm/pgtable.c`): stores the entry
  only when `dirty` is non-zero; returns non-zero whenever the entry differs,
  stored or not.
- Write-permission upgrade: pass a non-zero `dirty`, as `wp_page_reuse()` does;
  with `dirty` 0 x86 leaves the old entry in place.
- Generic `ptep_set_access_flags()` (`mm/pgtable-generic.c`): on a change calls
  `flush_tlb_fix_spurious_fault()`, whose default in `include/linux/pgtable.h`
  is `flush_tlb_page()`, not a local-only flush.
- `flush_tlb_fix_spurious_fault()` overrides, for example: empty on x86 and
  powerpc book3s64; local-only (`TLBF_NOBROADCAST`) on arm64.
- `handle_pte_fault()` with an unchanged entry: calls `fix_spurious_fault()` in
  `mm/memory.c`, which does nothing when `FAULT_FLAG_TRIED` is set or
  `FAULT_FLAG_WRITE` is clear.
- PMD level: `fix_spurious_fault()` calls `flush_tlb_fix_spurious_fault_pmd()`,
  a no-op by default; arm64 defines it.
- `pte_needs_flush()` generic (`include/asm-generic/tlb.h`): returns `true`
  always, so `change_pte_range()` queues every present entry it commits.
- `pte_needs_flush()` on x86 (`arch/x86/include/asm/tlbflush.h`): `false` when
  the old entry lacks `_PAGE_PRESENT`; otherwise any change of `_PAGE_RW`,
  `_PAGE_NX` or `_PAGE_USER`, in either direction, flushes; so read-only to
  writable through mprotect is flushed.
- x86 `pte_needs_flush()` otherwise skips the flush, among the flags that
  `pte_flags_need_flush()` names, only for: setting `_PAGE_DIRTY` or
  `_PAGE_ACCESSED`, clearing `_PAGE_ACCESSED`, software bits.
- `huge_pmd_needs_flush()` on x86: clearing `_PAGE_ACCESSED` does flush.
- `pte_needs_flush()` on arm64: any difference outside `PTE_SWBITS_MASK` on a
  valid entry flushes, upgrades included.
- `pte_needs_flush()` on powerpc book3s64 radix: the one override that skips a
  pure permission upgrade (`_PAGE_RWX`); it also skips setting `_PAGE_DIRTY`
  or `_PAGE_ACCESSED`.
- Dirty to clean: there is no ptep_clear_flush_dirty() here;
  `page_vma_mkclean_one()` in `mm/rmap.c` uses `ptep_clear_flush()`, then
  `set_pte_at()` with the write-protected clean entry.
- `ptep_clear_flush_young()`: generic flushes with `flush_tlb_page()` when the
  bit was set; the x86 override never flushes; x86 `pmdp_clear_flush_young()`
  does flush.
- `ptep_clear_flush()` generic: flushes only if `pte_accessible()`; on x86 a
  `PROT_NONE` entry is accessible only while `mm->tlb_flush_pending` is
  non-zero.

**Flush before dropping the lock**

- `force_flush` in the zap path: set in two places only, both in
  `zap_present_folio_ptes()` in `mm/memory.c`.
  - dirty entry of a non-anon folio, when `tlb_delay_rmap()` yields `true`;
  - `__tlb_remove_folio_pages()` returns `true` (batch full), which also sets
    `force_break`.
- `tlb_delay_rmap()`: sets `tlb->delayed_rmap`; `__tlb_remove_folio_pages()`
  only tags the page with `ENCODED_PAGE_BIT_DELAY_RMAP`, it does not report it.
- `tlb_delay_rmap()` without `CONFIG_SMP`, or with
  `CONFIG_MMU_GATHER_NO_GATHER` (s390 selects it): constant `false` in
  `include/asm-generic/tlb.h`; rmap is removed at once under the PTL and a
  dirty entry forces no flush.
- `tlb_flush_rmaps()`: walks only `tlb->local` and `tlb->active`;
  `tlb_next_batch()` refuses a new batch while `tlb->delayed_rmap` is set and
  `tlb->active` is not `tlb->local`, which is what forces the batch-full
  flush.
- `zap_empty_pte_table()`: clears the PMD entry while the PTE lock is still
  held, before the forced flush; skipped after `need_resched()` or
  `force_break`.
- Emptied PTE table: handed to `pte_free_tlb()` after `pte_unmap_unlock()`;
  it sets no `force_flush` and waits for the gather.
- `move_ptes()` flush placement: tied to the old and the new PTL; both are
  released only after `flush_tlb_range()` on the old range.
- `move_ptes()` rmap locks: `take_rmap_locks()` first, `drop_rmap_locks()` last,
  when `pmc->need_rmap_locks`; they bracket the whole function, error paths
  included, not the flush in particular.
- `pmc->need_rmap_locks`: a field of `struct pagetable_move_control` in
  `mm/internal.h`, not a parameter of `move_ptes()`.
- Lazy MMU mode: `zap_pte_range()` and `move_ptes()` both call
  `lazy_mmu_mode_disable()` before the flush.

**Reclaim's deferred flushes**

- `flush_tlb_batched_pending()` in `mm/rmap.c`: calls `flush_tlb_mm()`
  directly; there is no arch_flush_tlb_batched_pending() here.
- `mm->tlb_flush_batched`: the field `flush_tlb_batched_pending()` tests; it
  packs a pending and a flushed count, see `TLB_FLUSH_BATCH_FLUSHED_SHIFT`.
- `mm->tlb_flush_pending`: a separate counter, raised by `tlb_gather_mmu()`
  through `inc_tlb_flush_pending()`; `flush_tlb_batched_pending()` does not
  read it.
- Without `CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH`:
  `flush_tlb_batched_pending()` is an empty stub in `mm/internal.h` and
  `mm->tlb_flush_batched` does not exist.
- Producers: `set_tlb_ubc_flush_pending()` is called from `try_to_unmap_one()`
  and from `try_to_migrate_one()`; the entry left behind may be a migration
  entry.
- `TTU_BATCH_FLUSH` outside reclaim: passed for example by `unmap_folio()` in
  `mm/huge_memory.c`.
- `set_tlb_ubc_flush_pending()`: returns without recording anything when
  `!pte_accessible()`.
- `should_defer_flush()`: also needs `arch_tlbbatch_should_defer()`; on x86
  that is `true` only if another CPU is in `mm_cpumask()`.
- Level: both `set_tlb_ubc_flush_pending()` calls are on the `pvmw.pte` branch;
  all seven `flush_tlb_batched_pending()` call sites are PTE loops, none is in
  `mm/huge_memory.c`.
- Position: every call site sits between taking the PTL and
  `lazy_mmu_mode_enable()`.
- Relock in `madvise_free_pte_range()` and
  `madvise_cold_or_pageout_pte_range()`:
  - `start_pte` takes the result of the relock, so a failed relock can `break`
    and the exit path, which tests `start_pte`, skips `pte_unmap_unlock()`;
  - `nr = 0` after a successful `split_folio()`, so the same slot is read
    again with `ptep_get()`.
- **Unsafe usage**: calling `flush_tlb_batched_pending()` before the PTL is
  held, or once ahead of a loop that drops and retakes the PTL.
  - Safe: one call per lock acquisition, as `zap_pte_range()` does by jumping
    back to its `retry` label.
  - Safe: one call in a function that never drops the PTL, as
    `change_pte_range()` does.
  - Safe: with two tables, one call after both PTLs are held, as `move_ptes()`
    does after `spin_lock_nested()` on the new PTL.

## Kernel tables and lazy MMU mode

**Lazy MMU mode**

- Locks and preemption: the four helpers take no lock and do not touch
  preemption themselves; only the arch hooks they call may (see the
  sleeping rule below); `apply_to_pte_range()` and `vmap_pte_range()` take no
  lock before they enter the section for `init_mm`.
- Read-back on Xen PV: `xen_batched_set_pte()` in `arch/x86/xen/mmu_pv.c`
  queues the write and memory is not updated, so `ptep_get()` returns the old
  entry until the flush.
- Nesting: counted in generic code, in `enable_count` and `pause_count` of
  `struct lazy_mmu_state` (`include/linux/mm_types_task.h`), a field of
  `struct task_struct`; code in a section may call code that opens its own.
- `lazy_mmu_mode_pause()` and `lazy_mmu_mode_resume()`: defined beside
  `lazy_mmu_mode_enable()`; between them enable and disable do nothing.
- Making a write take effect mid-section from generic code: use pause/resume,
  or a nested enable/disable pair; `arch_flush_lazy_mmu_mode()` has no generic
  stub, so generic code that calls it builds only where the architecture
  defines it.
- `pte_fn_t` callbacks of `apply_to_page_range()`: run with the mode active;
  `apply_to_pte_range()` enables it around the loop and never pauses.
- `kasan_populate_vmalloc_pte()` and `kasan_depopulate_vmalloc_pte()`: pause
  around their own `ptep_get()` and PTE write; that is where the pause pattern
  is, not in `apply_to_pte_range()`.
- Interrupt entry: nothing flushes or pauses the interrupted task's batch;
  the helpers return at once and `is_lazy_mmu_mode_active()` returns false,
  so writes made from the interrupt are not batched.
- `in_interrupt()`: also true while bottom halves are disabled, so a section
  opened under `spin_lock_bh()` batches nothing.
- Context switch on Xen PV: `xen_start_context_switch()` calls
  `__task_lazy_mmu_mode_pause()` on `prev`, `xen_end_context_switch()` calls
  `__task_lazy_mmu_mode_resume()` on `next`; no thread flag is used.
- arm64 `TIF_LAZY_MMU_PENDING`: only records that barriers are owed; whether
  the mode is active comes from `is_lazy_mmu_mode_active()`.
- `is_lazy_mmu_mode_active()`: defined in `include/linux/sched.h` only under
  `CONFIG_ARCH_HAS_LAZY_MMU_MODE`, with no stub, so a caller builds only
  under that option.
- **Potentially unsafe usage**: sleeping inside a section.
  - Unsafe: in generic code; `arch_enter_lazy_mmu_mode()` calls
    `preempt_disable()` on sparc and on powerpc when `radix_enabled()` is
    false.
  - Safe: leave the outermost section before sleeping and re-enter after, as
    `madvise_cold_or_pageout_pte_range()` does around `split_folio()`; only
    the outermost `lazy_mmu_mode_disable()` calls
    `arch_leave_lazy_mmu_mode()`.
  - Safe: arm64-only code, where `arch_enter_lazy_mmu_mode()` is empty, as in
    `split_kernel_leaf_mapping()` in `arch/arm64/mm/mmu.c`.
- **Unsafe usage**: `lazy_mmu_mode_enable()` and its
  `lazy_mmu_mode_disable()` called with different `in_interrupt()` values, for
  example enable, then `spin_lock_bh()`, then disable; the disable returns
  before it decrements `enable_count` and `arch_leave_lazy_mmu_mode()` never
  runs.
  - Safe: both calls inside the same lock, as `zap_pte_range()` does; the
    `in_interrupt()` test at the top of both helpers defines the requirement.

**Populating kernel tables**

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

**Walking kernel tables**

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

## The page table checker

**Page table check hooks**

- Hook names: there is no page_table_check_pte_set() and no
  page_table_check_zero() here. The PTE set hook is
  `page_table_check_ptes_set()`; the free/alloc check is
  `__page_table_check_zero()`, reached through `page_table_check_free()` and
  `page_table_check_alloc()`.
- Set hooks `page_table_check_ptes_set()`, `page_table_check_pmds_set()`,
  `page_table_check_puds_set()`: take `(mm, addr, pointer, entry, nr)`.
  `page_table_check_pmd_set()` and `page_table_check_pud_set()` are macros
  that pass `nr` = 1.
- Clear hooks: take `(mm, addr, old entry)`.
- `pte_user_accessible_page()` and the pmd/pud forms: take `(mm, addr, entry)`.
- Set hook on a populated slot: runs the clear accounting for the old entries
  it reads through the pointer, then counts the new one. A helper that
  replaces an entry in place calls the set hook only.
- Anon write test in `page_table_check_set()`: looks only at the write bit of
  the entry being installed. A read-only second mapping of an anon page whose
  first mapping is writable passes.
- Write test: runs only inside a set hook. x86 `ptep_set_access_flags()`
  stores with `set_pte()`, so a write upgrade there is not tested.
- Flag checks `page_table_check_pte_flags()`, `page_table_check_pmd_flags()`:
  `WARN_ON_ONCE()`, not `BUG_ON()`. They fire for a uffd-marked entry that is
  writable, or a uffd-marked swap entry that is a writable migration or
  device-private entry. `__page_table_check_puds_set()` has no flag check.
- Not counted even when user-accessible: PTEs with `pte_special()`, PMDs that
  map the huge zero folio (`page_table_check_huge_zero_pmd()`), and pfns
  failing `pfn_valid()`.
- `PageSlab()` page reaching `page_table_check_set()`,
  `page_table_check_clear()` or `__page_table_check_zero()`: `BUG_ON()`.
- `set_pmd_at()`, `set_pud_at()`: no generic definition; each architecture
  defines its own and must call the hook itself.
- Generic `ptep_set_wrprotect()` in `include/linux/pgtable.h`: goes through
  `set_pte_at()`, so it runs the set hook. The x86, arm64 and riscv overrides
  do not.
- arm64: the hooks are inside `__set_ptes_anysz()` and
  `__ptep_get_and_clear_anysz()`, so `__set_ptes()`, `__set_pmds()`,
  `__set_puds()` and `__ptep_get_and_clear()` are already hooked. `__set_pte()`
  and `__pte_clear()` are raw. A leading underscore does not tell which.
- In-place update that makes a counted entry non-accessible: must be
  accounted as a clear. Generic `pmdp_invalidate()` in
  `mm/pgtable-generic.c` gets it from the set hook in `pmdp_establish()`.
- `page_table_check_pte_clear_range()`: needed because a table PMD fails
  `pmd_user_accessible_page()`, so the PMD clear hook counts nothing for the
  PTEs below it. Pass the old PMD value after the slot is cleared, before the
  table is freed, as `retract_page_tables()` in `mm/khugepaged.c` does.
- `ARCH_SUPPORTS_PAGE_TABLE_CHECK`: also selected by s390, and by powerpc only
  `if !HUGETLB_PAGE`.
- **Unsafe usage**: calling a set hook after the new entry is stored. The hook
  then un-counts the new page instead of the old one.
  - Safe: hook first, then store, as `set_ptes()` in
    `include/linux/pgtable.h`; `__page_table_check_ptes_set()` reads the old
    entries with `ptep_get()`.
- **Unsafe usage**: calling a hook for a change that a callee already
  reported. A set hook ahead of a hooked setter counts the page twice; a
  second clear makes `page_table_check_clear()` hit `BUG_ON()` on a negative
  count.
  - Safe: rely on the hooked callee, as `ptep_clear_flush()` in
    `mm/pgtable-generic.c` relies on `ptep_get_and_clear()`.
- **Potentially unsafe usage**: writing a user entry with a raw store,
  `xchg()` or cmpxchg and no hook.
  - Unsafe: when the write changes the pfn, or changes what
    `pte_user_accessible_page()` (or the pmd/pud form) returns, in an mm other
    than `init_mm`. The counts drift and a later `page_table_check_clear()` or
    `__page_table_check_zero()` hits `BUG_ON()`.
  - Safe: when pfn and user-accessibility stay the same, as x86
    `ptep_set_wrprotect()`. `__page_table_check_ptes_set()` and
    `__page_table_check_pte_clear()` count by `pte_pfn()` and only for entries
    that pass `pte_user_accessible_page()`.

## Model gaps

### Other mistakes models make

- Models take GUP on a protnone entry to depend on `FOLL_HONOR_NUMA_FAULT`
  only. `gup_can_follow_protnone()` in `include/linux/mm.h` returns false first
  for an accessible `VM_UFFD_RWP` VMA.
- Models do not know `sync_with_folio_pmd_zap()` in `mm/internal.h`: a folio
  unmap that finds `pmd_none()` without the lock takes and drops the PMD lock,
  so a concurrent `zap_huge_pmd()` has removed the rmap. `zap_pmd_range()` and
  `page_vma_mapped_walk()` call it.
- Models write the uffd support test as pgtable_supports_uffd_wp(). The test
  for marker support here is `uffd_supports_wp_marker()` in
  `include/asm-generic/pgtable_uffd.h`.
- Models test VMA flags only as `vma->vm_flags & VM_WRITE`, and COW with
  is_cow_mapping(). `struct vm_area_struct` holds a union of `vm_flags` and the
  bitmap `flags`; `vma_test()` and `vma_test_any_mask()` are the same tests,
  and COW is `vma_is_cow_mapping()`.
- Models raise the swap count at unmap with swap_duplicate(). Here
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c` calls `folio_dup_swap()`.
- Models take `folio_referenced_one()` to clear young one PTE at a time. It
  calls `clear_flush_young_ptes_notify()`, or `lru_gen_look_around()` under
  MGLRU, on a `folio_pte_batch()` run.
- Models do not know `ptep_try_set()` in `include/linux/pgtable.h`: an atomic
  install into an empty PTE; `flush_tlb_before_set()` is the flush made after
  a populated entry is cleared, before the retry. Both are called only from
  `kernel/bpf/arena.c`, for kernel tables. The generic `ptep_try_set()`
  returns false; x86 overrides it, arm64 only under `CONFIG_ARM64_CONTPTE`.
- Models take `remap_pfn_range()` to be the only way to map PFNs at mmap time.
  A `mmap_prepare` hook gets a `struct vm_area_desc` and no VMA;
  `remap_pfn_range_complete()` in `mm/memory.c` maps once the VMA exists.
- Models do not know that `try_to_unmap()` sends hugetlb folios to
  `try_to_unmap_poisoned_hugetlb_one()` and not to `try_to_unmap_one()`.
