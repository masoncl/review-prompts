# What the mm-pagetable measurement found

Three models were asked the 88 questions in `mm-pagetable-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-pagetable.md` holds the questions it does. The readers are labelled A, B
and C. Reader C is the most current (it assumed 6.15 to 7.1), reader A sits a
few releases behind it (6.12 to 6.19) and reader B is the oldest (6.10 to 6.13).
Which models they were does not matter here.

## How it compares with the other mm guides

Readers A and C know the concepts and most of the structure: the four PTE
mapping helpers, the batching flags, the kinds of non-present entry, the
mmu_gather API. What they get wrong is what moved recently, and a good deal
moved: one bit was renamed and gained a second user, the whole zap family was
renamed, a file they all cite does not exist. Reader B is wrong about
fundamentals as well, so almost nothing is known to every reader. As with
`mm-folio`, the build set was chosen by importance within the size of the
hand-written guide, with small budgets where A and C are already right.

## What every reader got wrong

- **The userfaultfd bit was renamed and has two users.** All three gave
  pte_uffd_wp(), pte_mkuffd_wp(), pte_swp_uffd_wp(), pte_clear_uffd_wp() and
  pgtable_supports_uffd_wp(). The tree has `pte_uffd()`, `pte_mkuffd()`,
  `pte_clear_uffd()`, `pte_swp_uffd()`, `pte_swp_mkuffd()`, the `pmd_` forms
  and `pgtable_supports_uffd()`. All three said only write-protect mode uses
  the bit, and none knew the RWP mode (`VM_UFFD_RWP`, `MM_CP_UFFD_RWP`,
  `userfaultfd_pte_rwp()`), which puts the same bit on top of a no-access
  entry. So none knew that `do_swap_page()`, `restore_exclusive_pte()`,
  `remove_migration_pte()`, `unuse_pte()` and `change_present_ptes()` re-apply
  `PAGE_NONE`, that `move_ptes()` puts the VMA's own protection back when the
  destination drops the registration, or that a protnone entry now has two
  possible meanings.
- **Reclaim of empty PTE tables is not where they think.** All three put it in
  mm/pt_reclaim.c with try_get_and_clear_pmd(), try_to_free_pte() and
  free_pte(). That file is not in the tree. The code is
  `pte_table_reclaim_possible()`, `zap_empty_pte_table()` and
  `zap_pte_table_if_empty()` in `mm/memory.c`, and `zap_pte_range()` does the
  `pte_free_tlb()` itself. Reader B doubted that zap-time reclaim exists.
- **The zap family.** zap_page_range_single(), zap_page_range_single_batched(),
  zap_vma_ptes(), unmap_page_range() and unmap_single_vma() are gone. The tree
  has `zap_vma_range()`, `zap_vma_range_batched()`, `zap_special_vma_range()`,
  `zap_vma_for_reaping()` and the worker `__zap_vma_range()`. Reader C had the
  new names when asked for them and the old ones in three other answers.
  `unmap_vmas()` and `free_pgtables()` take a `struct unmap_desc`, which A and
  B did not know. `struct zap_details` has `skip_cows` (not even_cows) and a
  `reaping` field.
- **The special bit by level.** None knew `pgtable_level_has_pxx_special()`:
  the PTE level depends on `CONFIG_ARCH_HAS_PTE_SPECIAL`, PMD and PUD on
  `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP` and `CONFIG_ARCH_SUPPORTS_PUD_PFNMAP`. A
  and B called the VMA hook find_special_page(); it is `find_normal_page()`
  under `CONFIG_FIND_NORMAL_PAGE`. Reader A had the PFNMAP rule as "and" where
  the code has "or".
- **What the huge PMD lock accepts.** All three gave is_swap_pmd() ||
  pmd_trans_huge(). The predicate is `pmd_is_huge()` in
  `include/linux/huge_mm.h`: any non-none, non-present PMD passes.
- **Configuration names.** CONFIG_ARCH_ENABLE_THP_MIGRATION is
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`, CONFIG_PTDUMP_CORE is `CONFIG_PTDUMP`,
  CONFIG_SPLIT_PTLOCK_CPUS is `CONFIG_SPLIT_PTE_PTLOCKS` (B and C), and
  `CONFIG_DEBUG_VM_PGTABLE` lives in `lib/Kconfig.debug`.
- **When the table batch cannot be allocated.** All three said the fallback is
  an IPI through `tlb_remove_table_sync_one()`. `__tlb_remove_table_one()`
  uses `call_rcu()` on the ptdesc with `CONFIG_PT_RECLAIM`, and
  `tlb_remove_table_sync_rcu()`, a `synchronize_rcu()`, without it. All three
  left `tlb_remove_table_sync_rcu()` out of the helpers that must not be used
  for freeing.
- **Smaller things all three missed.** The swap-format entry is built by
  `swp_pte_prepare()`, not inline in `try_to_unmap_one()`. Swap slots are
  released with `swap_put_entries_direct()`; free_swap_and_cache_nr() is gone.
  `struct ptdesc` starts with `pt_flags`, not __page_flags.
  `tlb_gather_mmu_vma()` and the `unshared_tables` fields of
  `struct mmu_gather`. `walk_kernel_page_table_range_lockless()`, and that
  `walk_page_range_debug()` asserts the write lock on both the mm and
  `init_mm`. The VMA test callback is never called by the single-VMA walks, and
  a positive return from it ends a `walk_page_mapping()` walk.
  `folio_can_map_prot_numa()` is in `mm/mempolicy.c` and its skip rules.

## What readers A and B got wrong as well

- **Old swap-entry helpers in every usage answer.** Reader A described the
  `softleaf_t` API correctly when asked about it, then wrote is_swap_pte(),
  is_pfn_swap_entry(), pfn_swap_entry_to_page(), swp_offset_pfn(),
  is_writable_migration_entry() and is_pmd_migration_entry() in five other
  answers. None of those exist. Reader B did not know the API at all.
- **Fork's batch flags.** `copy_present_ptes()` always passes `FPB_MERGE_WRITE`
  and never `FPB_RESPECT_WRITE`; both had it otherwise.
- **The fresh anonymous entry** is built by `map_anon_folio_pte_nopf()`, shared
  with `collapse_huge_page()`, not in `do_anonymous_page()`.
- **`folio_walk_start()`** has one flag, `FW_ZEROPAGE`. Both invented
  FW_MIGRATION. It needs the mmap lock; a per-VMA lock is not enough.
- **Markers.** Reader A had the uffd-wp marker fault backwards: an armed VMA
  goes to `do_pte_missing()`, an unarmed one has the marker cleared. Reader B
  named PTE_MARKER_SWAPIN_ERROR for `PTE_MARKER_POISONED`.
  `ZAP_FLAG_DROP_MARKER` governs guard markers too.
- **`restore_exclusive_pte()` and `remove_migration_pte()`.** The first makes
  the entry writable from `VM_WRITE` and `can_change_pte_writable()`, not from
  the old entry. The second sets dirty only when the entry and the folio are
  both dirty, and gives write only for a writable entry.
- **Lazy MMU mode.** Only the outermost section calls the enter and leave
  hooks; a nested leave flushes; the state is `current->lazy_mmu_state`; x86
  has the mode only with `PARAVIRT_XXL`.

## What reader B got wrong alone: fundamentals

- With no flags the batching helper compares the write bit. It does not: write,
  dirty, soft-dirty and accessed are all ignored. It also named flags
  FPB_IGNORE_DIRTY and FPB_IGNORE_SOFT_DIRTY, which do not exist.
- Device-private and device-exclusive entries hold no reference or mapcount.
  They hold both, and the zap drops both.
- The nolock mapping helpers need no unmap, and `pte_offset_map_lock()` returns
  NULL when its recheck fails. They hold RCU and need `pte_unmap()`; the
  locking helper retries.
- `PGWALK_RDLOCK` takes the mmap lock. The walker only asserts it.
- Installing an entry needs a per-VMA write lock, and the reverse-map locks are
  not enough to traverse or zap. Reading or writing mode of the mmap or VMA
  lock installs; any of the three traverses and zaps.
- A move only preserves soft-dirty. `move_soft_dirty_pte()` sets it.
- A clean writable entry is forbidden in a shared mapping that wants write
  notification. Fork creates one; what is forbidden is upgrading a clean entry
  to writable.
- There is a devmap bit and a pfn_t. Neither exists.
- `filemap_page_mkwrite()` takes no freeze protection. It takes
  `sb_start_pagefault()`.

## What reader C got wrong that A did not

`vmf_insert_mixed()` marks every PFN special when the architecture has the
bit, not only PFNs without a struct page. A read-back inside a lazy MMU section
is stale only on Xen PV; arm64 writes the entry at once and defers barriers.
`pte_unmap()` without `CONFIG_HIGHPTE` only drops the RCU read lock.

## What the readers already knew

Readers A and C: the files and entry points apart from the two renames, the
documentation, the four PTE mapping helpers and when they return NULL, how a
new table is installed, the kinds of non-present entry, which carry a PFN, the
batching flags, what the default comparison ignores and how to bound a batch,
the mmu_gather functions, which transitions need a flush, how to populate
kernel tables, special versus normal entries and the present-only accessors.
Reader C also knew the soft-dirty rule on move and the write-permission gate.
In the build set these keep their place, with small budgets, because reader B
is wrong on most of them.

## Where the hand-written guide stands

`mm-pagetable.md` was checked line by line against this tree, and the
measurement found nothing in it that is wrong. What it lacks is what the
readers needed most: it has no map of the files, and it never says that the
userfaultfd accessors, the swap-entry helpers and the zap functions have new
names, because it simply uses the new ones. It carries one commit SHA, which a
built guide may not. Its item on bit locks is about reclaim, not page tables,
and was not carried over. Its remark that lazy MMU bugs show on arm64 is true
of sleeping and pairing but not of stale reads.

## Left out of the build set

For space: the documentation list, reading and writing entries, atomicity and
the lockless readers, `pte_mkwrite()` and the VMA, device memory entries, which
kinds carry a PFN, the fresh anonymous entry, the protection change flags,
which lock covers which level, what a mapping holds between map and unmap,
installing a table, moving tables, walker actions, `folio_walk_start()`, the
GUP-fast walk, hugetlb entries, hand-written batch loops, freeing kernel tables
and adding an architecture helper. If a build comes in well under its size,
atomicity, `folio_walk_start()` and the GUP-fast walk are the first to bring
back.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too, so it overstates
reader B's gap; the corrections are what count.

```
reader A: 192 corrections, 32% rewritten on average
reader B: 224 corrections, 75% rewritten on average
reader C: 160 corrections, 23% rewritten on average

question                                reader A      reader B      reader C
pagetable.core-files                    10% ( 2)      11% ( 5)       6% ( 4)
pagetable.entry-points                   1% ( 1)      18% ( 3)       5% ( 2)
pagetable.docs                           0% ( 0)      17% ( 1)      10% ( 1)
pagetable.debug-and-tests               45% ( 3)      69% ( 3)      36% ( 2)
pagetable.entry-read-write              23% ( 3)      85% ( 5)      33% ( 1)
pagetable.atomicity                     28% ( 2)      67% ( 3)      46% ( 2)
pagetable.lockless-reads                30% ( 1)      90% ( 2)      49% ( 1)
pagetable.pte-mkwrite-vma                7% ( 1)      77% ( 1)      15% ( 1)
pagetable.special-bit                   68% ( 4)      92% ( 2)      61% ( 3)
pagetable.normal-page-lookup            33% ( 4)      68% ( 5)      20% ( 4)
pagetable.device-memory-entries         23% ( 1)      77% ( 2)       0% ( 0)
pagetable.uffd-bit                      58% ( 5)      75% ( 3)      63% ( 2)
pagetable.soft-dirty-support            26% ( 1)      77% ( 1)      16% ( 0)
pagetable.nonpresent-api                45% ( 1)      88% ( 4)      20% ( 7)
pagetable.nonpresent-kinds               0% ( 0)      55% ( 1)       0% ( 0)
pagetable.markers                       43% ( 4)      74% ( 1)      22% ( 1)
pagetable.pmd-nonpresent                31% ( 1)      92% ( 1)       2% ( 1)
pagetable.nonpresent-has-pfn            24% ( 1)      78% ( 1)       0% ( 0)
pagetable.nonpresent-refs                7% ( 2)      91% ( 1)      42% ( 2)
pagetable.swap-pte-bits                 21% ( 2)      81% ( 6)      11% ( 5)
pagetable.migration-ad-bits             34% ( 3)      87% ( 3)      20% ( 2)
pagetable.nonpresent-dispatch-usage     17% ( 1)      89% ( 3)      32% ( 3)
pagetable.nonpresent-to-present         51% ( 6)      86% ( 5)      18% ( 2)
pagetable.nonpresent-rewrite            45% ( 4)      88% ( 4)      50% ( 2)
pagetable.write-dirty-combinations      44% ( 4)      70% ( 6)      15% ( 3)
pagetable.young-dirty                   31% ( 1)      87% ( 1)      25% ( 1)
pagetable.fresh-anon-pte                64% ( 1)      70% ( 2)      31% ( 1)
pagetable.lazyfree-pte                  31% ( 1)      87% ( 2)       9% ( 1)
pagetable.vm-write-gate                 53% ( 1)      90% ( 2)       3% ( 1)
pagetable.uffd-rwp-protnone             87% ( 1)      90% ( 2)      88% ( 1)
pagetable.numa-hint                     59% ( 3)      86% ( 5)      45% ( 4)
pagetable.change-prot-flags             72% ( 2)      80% ( 1)      41% ( 1)
pagetable.soft-dirty-on-move            36% ( 1)      82% ( 1)       0% ( 0)
pagetable.vma-flag-bits                 56% ( 4)      87% ( 1)      31% ( 1)
pagetable.present-only-accessors        19% ( 1)      74% ( 1)      19% ( 1)
pagetable.special-usage                 22% ( 1)      73% ( 1)       6% ( 0)
pagetable.ptdesc                        38% ( 4)      75% ( 4)      19% ( 4)
pagetable.split-locks                   15% ( 1)      74% ( 2)      11% ( 1)
pagetable.pte-map-variants               4% ( 1)      68% ( 2)       0% ( 0)
pagetable.pte-map-null                   3% ( 1)      80% ( 1)       0% ( 0)
pagetable.pte-map-rcu                   16% ( 2)      83% ( 1)      38% ( 1)
pagetable.pte-unmap-pointer              5% ( 1)      64% ( 1)      45% ( 4)
pagetable.install-table                  0% ( 0)      42% ( 1)       0% ( 0)
pagetable.populate-lock-rule            44% ( 1)      61% ( 3)      23% ( 1)
pagetable.free-pgtables                 59% ( 1)      75% ( 2)      57% ( 3)
pagetable.empty-table-reclaim           38% ( 2)      88% ( 3)      52% ( 3)
pagetable.recheck-after-relock          45% ( 1)      91% ( 3)      57% ( 4)
pagetable.vma-lock-and-tables           31% ( 3)      70% ( 2)      13% ( 1)
pagetable.move-tables                   38% ( 1)      83% ( 3)      37% ( 1)
pagetable.pmd-lock-accepts              55% ( 2)      84% ( 1)      11% ( 1)
pagetable.fault-lock-order              32% ( 1)      75% ( 5)      35% ( 1)
pagetable.walk-ops                      34% ( 4)      64% ( 4)      39% ( 4)
pagetable.walk-entry-points             15% ( 3)      77% ( 4)      47% ( 2)
pagetable.walk-lock                     24% ( 1)      89% ( 3)      21% ( 1)
pagetable.walk-actions                  33% ( 1)      70% ( 1)      24% ( 1)
pagetable.walker-returns                62% ( 1)      55% ( 2)      30% ( 1)
pagetable.walker-pmd-entry              16% ( 1)      40% ( 2)      39% ( 1)
pagetable.walker-default-vmas           29% ( 1)      47% ( 1)       0% ( 0)
pagetable.walker-again-usage            34% ( 1)      72% ( 2)      29% ( 1)
pagetable.folio-walk                    42% ( 6)      75% ( 1)      26% ( 3)
pagetable.pvmw-state                    29% ( 2)      74% ( 1)      11% ( 1)
pagetable.pvmw-nonpresent               31% ( 2)      60% ( 1)      11% ( 1)
pagetable.pvmw-accessor-usage           43% ( 5)      75% ( 1)       8% ( 1)
pagetable.gup-fast-walk                 38% ( 3)      74% ( 1)      30% ( 1)
pagetable.hugetlb-differences           47% ( 2)      79% ( 1)      42% ( 1)
pagetable.batch-flags                    0% ( 0)      77% ( 4)       8% ( 1)
pagetable.batch-default-ignores          7% ( 1)      69% ( 1)       0% ( 0)
pagetable.batch-writeback-usage         28% ( 4)      80% ( 1)      41% ( 4)
pagetable.batch-bounds                  11% ( 1)      76% ( 1)       6% ( 1)
pagetable.batch-helpers                 27% ( 4)      75% ( 7)       8% ( 2)
pagetable.batch-handrolled               0% ( 0)      76% ( 1)       0% ( 0)
pagetable.large-folio-install           26% ( 2)      82% ( 3)      16% ( 1)
pagetable.tlb-flush-rules               20% ( 1)      80% ( 3)      10% ( 1)
pagetable.tlb-flush-before-unlock       40% ( 4)      89% ( 2)      20% ( 3)
pagetable.mmu-gather-api                 8% ( 1)      83% ( 2)       7% ( 1)
pagetable.batched-flush-pending         19% ( 2)      85% ( 3)      36% ( 3)
pagetable.zap-api                       60% ( 9)      84% ( 7)      21% ( 6)
pagetable.zap-details                   53% ( 2)      84% ( 2)      33% ( 3)
pagetable.table-free-configs            43% ( 5)      70% ( 6)      35% ( 6)
pagetable.table-free-vs-gup-fast        34% ( 4)      88% ( 3)      19% ( 4)
pagetable.kernel-table-free             63% ( 2)      92% ( 1)      23% ( 1)
pagetable.kernel-populate-sync          12% ( 2)      84% ( 4)      11% ( 3)
pagetable.kernel-walk-hotplug           30% ( 2)      83% ( 4)      22% ( 2)
pagetable.lazy-mmu-api                  50% ( 5)      78% ( 6)      11% ( 3)
pagetable.lazy-mmu-usage                51% ( 4)      79% ( 4)      23% ( 3)
pagetable.page-table-check-hooks        52% ( 4)      87% ( 4)      32% ( 3)
pagetable.arch-helper-change            29% ( 2)      60% ( 3)      14% ( 1)
pagetable.zeropage-compare              60% ( 2)      83% ( 2)      46% ( 1)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `pagetable.entry-read-write`, `pagetable.atomicity`, `pagetable.nonpresent-has-pfn`, `pagetable.split-locks`, `pagetable.pte-map-rcu`, `pagetable.gup-fast-walk`.
