# What the mm-largepage measurement found

Three models were asked the 90 questions in `mm-largepage-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-largepage.md` holds the questions it does. The readers are labelled A, B
and C; which models they were does not matter here. Readers A and C assumed a
kernel a few releases behind this tree and B an older one still. Reader C needed
the fewest corrections, reader B the most. The hand-written guide was one of the
six checked against current sources, so it was used as a reference for facts as
well as for its size of 3,067 words.

## What all three readers got wrong

- **The deferred split queue is a different data structure.** All three
  described struct deferred_split, split_queue_lock and a queue in each node
  and memory cgroup. None of that exists. The queue is `deferred_split_lru`, a
  memcg-aware `struct list_lru`; a folio's entry is protected by the lock of
  its `struct list_lru_one`; and only anonymous folios of order two and up are
  ever queued, and not while they are in the swap cache. The readers gave the
  wrong reason for not unqueueing a folio that still has references: it is the
  shrinker's unlocked on-stack list, not a racing requeue.
- **`folio_memcg_alloc_deferred()` was unknown to all three**, and with it the
  rule that a site which allocates and charges a large anonymous folio must call
  it (for order above one) before the folio can be queued. One reader offered
  folio_prep_large_rmappable(), which is not in the tree.
  `map_anon_folio_pmd_nopf()` and `map_anon_folio_pte_nopf()` were not
  recognised either, nor that the counters live in the `_pf` wrappers.
- **The collapse daemon collapses to orders below a PMD.** All three said this
  was not merged. The tree has `mthp_collapse()`, a bitmap of present PTEs
  filled by `collapse_scan_pmd()`, `KHUGEPAGED_MIN_MTHP_ORDER`, and an order
  argument on `collapse_huge_page()`. All three scaled the empty-PTE limit
  proportionally; `collapse_max_ptes_none()` allows empty PTEs below PMD order
  only when the setting is at its maximum, and the swap and shared limits are
  zero there.
- **The collapse functions are renamed.** khugepaged_scan_mm_slot() and the
  hpage_collapse_ names are gone; the chain is `collapse_scan_mm_slot()`,
  `collapse_single_pmd()`, then `collapse_scan_pmd()` or `collapse_scan_file()`.
- **File collapse eligibility.** All three cited CONFIG_READ_ONLY_THP_FOR_FS and
  a file not open for writing. Neither is in the tree. `file_thp_enabled()` asks
  `mapping_pmd_folio_support()`, that is, what the filesystem declared.
- **Huge PMD tests.** All three said `pmd_trans_huge()` is true only for a
  transparent huge page. It tests entry bits, so hugetlb, DAX and PFN leaves
  match too. `pmd_is_huge()`, which also accepts non-present entries and is what
  `split_huge_pmd()` and `pmd_trans_huge_lock()` use, was unknown to one reader
  and misplaced by another. The option for non-present huge PMDs is
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; all three named an option that no longer
  exists.
- **Splitting a file PMD installs no PTEs.** One reader had it add PTE mappings
  from a deposited table, and another had every file PMD keep such a table.
  `__split_huge_pmd_locked()` clears the entry, drops the PMD's rmap and
  reference, and lets the range fault back in; a file PMD has a deposited table
  only where `arch_needs_pgtable_deposit()` says so.
- **Split details.** A non-uniform split that runs out of memory in
  `xas_try_split()` leaves the folio partly split, where the readers said every
  failure leaves it whole. The count frozen is the cache references plus one,
  not the expected count (two readers). `min_order_for_split()` returns 0 for a
  truncated folio, not an error (two readers). `thp_underused()` compares with
  `pages_identical()`, and gives up on a folio that contains a poisoned page.
- **`try_to_unmap_one()` has no full hugetlb branch.** `try_to_unmap()` sends
  hugetlb folios to `try_to_unmap_poisoned_hugetlb_one()`. All three described a
  full branch in `try_to_unmap_one()`.
- **Hugetlb.** `hugetlb_alloc_folio()`, where the cgroup charges, the dequeue or
  surplus allocation and the reservation decrement now happen, was not
  recognised by two readers. "An error path re-adds a folio with the surplus
  value it removed it with" has exceptions: a failed restore of struct pages
  always re-adds as surplus. The struct page optimisation maps tail struct pages
  read-only onto a shared per-zone page from `vmemmap_get_tail()`, not onto the
  folio's first page. `page_is_unmovable()` computes the size from
  `compound_order()` and treats a missing hstate as unmovable.
- **Large folio swap-in.** Two readers described an older tree. Here
  `swapin_sync()` passes a mask of orders to `swap_cache_alloc_folio()`, which
  checks the range with `__swap_cache_add_check()` and falls back an order on
  -EBUSY or -ENOMEM.

## What readers A and B got wrong as well

- The rmap level is `enum pgtable_level`, not enum rmap_level, and there is no
  anonymous PUD add.
- `folio_split_unmapped()` is uniform, anonymous only, and leaves every piece
  locked.
- File collapse never freezes the old folios and stores the new folio once, at
  the end; they had it swap slots one by one and roll them back.
- In the hugetlb fault path the file rmap lock is taken, for read inside
  `huge_pmd_share()` and for write in `unmap_ref_private()`; one said never,
  the other said throughout.

## What reader B got wrong as well: fundamentals

- The hugetlb fault lock order: it put the folio lock inside the page table
  lock.
- `folio_split()` leaves the first piece locked for the caller, not the one that
  holds the split point.
- `memory_failure()` on a large folio splits to `min_order_for_split()`, treats
  any nonzero order as a failure, kills, and returns -EHWPOISON.
- A hugetlb folio is recognised by a page type, not by a compound destructor.
- `gbl_chg == 0` means a global reservation is used; it had this inverted.
- The exemption from the end-of-file mapping rule is shmem, not DAX.
- `PG_has_hwpoisoned` is on the first tail page, and `PG_hwpoison` is set on the
  bad page inside a large folio too.
- `unmap_poisoned_folio()` handles hugetlb and cannot handle other large
  folios; it had this the other way round.
- The index of a hugetlb folio in the page cache is in base pages:
  `hugetlb_add_to_page_cache()` shifts the index it is given.
- `huge_pmd_share()` takes the file rmap lock itself; callers hold only the
  hugetlb VMA lock.

## What the readers already knew

The files and most entry points (all three). Readers A and C also knew the
state tracking table, how transparent huge pages are disabled per process, the
poison flags, the non-atomic flag rule and the hugetlb per-folio flags. All
three were close on the pool counters.

## Where the hand-written guide is stale

It is current nearly everywhere. One item has moved: it points at
`try_to_unmap_one()` as a function with a full hugetlb branch, and in this tree
the hugetlb case of `try_to_unmap()` is `try_to_unmap_poisoned_hugetlb_one()`.
It has no map of the subsystem, and nothing on huge PMD entries, PMD splitting,
collapse, what the deferred split queue is, or what an allocation site must do,
which is where the readers were most wrong. Those take the place of what the
readers already know.

## Left out of the build set

Forty-four of the ninety questions, for space, within the size of the
hand-written guide:

- Known to readers A and C: disabling per process, the per-size controls, the
  flags on the first tail page, the pool counters, the hugetlb per-folio flags,
  natural alignment, and the anonymous exclusive flag on its own (it is a row of
  the state tracking table).
- Covered by a question that was kept: the anonymous fault paths and what an
  allocation site owes the deferred split queue (both asked for under adding an
  allocation site), THP and hugetlb PMDs (the huge PMD tests say it), the state
  carried to the pieces of a split (the poison part is under the poison flags),
  PMD table sharing (unsharing is kept and names the locks), unmapping a
  poisoned folio (under unmapping a PMD-mapped folio), the hugetlb poison records.
- Narrow, or of use to fewer reviewers: the kinds of large folio, shmem huge
  policy, the huge zero folio, the file PMD mapping, the write fault on a huge
  PMD, locking a huge PMD, split preconditions, the split sequence, uniform and
  non-uniform splits, pieces beyond end of file, zero-filled pieces, underused
  huge pages, the collapse thresholds, collapse and lockless walkers, file
  collapse, PTE-mapped file huge pages, collapse on request, the rmap calls by
  level, migration, hugetlb compared with THP, freeing a hugetlb folio, the
  hugetlb cgroup charges, the hugetlb VMA lock, hugetlb copy-on-write, walking
  hugetlb page tables, hugetlb migration, poison accounting, folios spanning
  range pieces, the documentation.

The readers were wrong about several of the narrow ones too. If a build has
room, the candidates to add back are the split sequence, file collapse, the
hugetlb VMA lock and hugetlb copy-on-write.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 195 corrections, 41% rewritten on average
reader B: 264 corrections, 77% rewritten on average
reader C: 172 corrections, 24% rewritten on average

question                                  reader A      reader B      reader C
largepage.core-files                       8% ( 1)      11% ( 1)       7% ( 1)
largepage.entry-points                    10% ( 4)       8% ( 2)      13% ( 3)
largepage.docs                            32% ( 0)      59% ( 3)      23% ( 0)
largepage.kinds                           33% ( 3)      87% ( 9)      29% ( 2)
largepage.allowable-orders                33% ( 2)      83% ( 3)      29% ( 2)
largepage.sysfs-controls                  23% ( 1)      80% ( 3)      20% ( 1)
largepage.thp-disable                      0% ( 0)      84% ( 3)       0% ( 0)
largepage.shmem-huge                      35% ( 1)      84% ( 4)      52% ( 1)
largepage.file-collapse-eligibility       76% ( 2)      89% ( 3)      70% ( 2)
largepage.anon-pmd-fault                  31% ( 6)      82% ( 5)      34% ( 3)
largepage.anon-mthp-fault                 37% ( 1)      82% ( 3)      10% ( 1)
largepage.huge-zero                       37% ( 1)      73% ( 3)       7% ( 1)
largepage.pgtable-deposit                 40% ( 1)      81% ( 2)      19% ( 1)
largepage.file-pmd-mapping                52% ( 1)      83% ( 3)      12% ( 1)
largepage.pmd-cow                         29% ( 1)      89% ( 2)      15% ( 1)
largepage.pmd-leaf-tests                  43% ( 1)      84% ( 4)      18% ( 3)
largepage.pmd-softleaf                    33% ( 2)      83% ( 3)      23% ( 3)
largepage.pmd-locking                     42% ( 1)      55% ( 1)       0% ( 0)
largepage.pmd-split                       42% ( 1)      88% ( 4)      31% ( 3)
largepage.huge-pmd-ambiguity              30% ( 1)      84% ( 2)      22% ( 1)
largepage.split-api                       33% ( 5)      60% ( 5)      16% ( 4)
largepage.split-preconditions             46% ( 1)      87% ( 1)      16% ( 1)
largepage.split-errors                    68% ( 1)      78% ( 1)      21% ( 3)
largepage.split-steps                     44% ( 1)      82% ( 1)      14% ( 2)
largepage.split-refcount                  60% ( 1)      89% ( 1)       8% ( 1)
largepage.split-retry-usage               28% ( 1)      77% ( 1)      34% ( 2)
largepage.split-min-order                 53% ( 5)      79% ( 3)      20% ( 4)
largepage.split-uniform                   49% ( 5)      87% ( 3)      22% ( 2)
largepage.split-beyond-eof                40% ( 2)      92% ( 2)       0% ( 0)
largepage.split-state-propagation         37% ( 3)      76% ( 2)       4% ( 3)
largepage.split-zeropage                  63% ( 5)      71% ( 3)      24% ( 2)
largepage.deferred-split-queue            78% ( 3)      82% ( 4)      54% ( 4)
largepage.deferred-split-queuers          43% ( 1)      76% ( 2)      45% ( 1)
largepage.deferred-split-unqueue          70% ( 1)      84% ( 1)      60% ( 1)
largepage.deferred-split-alloc            88% ( 1)      87% ( 1)      85% ( 1)
largepage.underused                       63% ( 1)      73% ( 0)      44% ( 0)
largepage.khugepaged-overview             61% ( 6)      74% ( 6)      21% ( 6)
largepage.collapse-anon-steps             49% ( 5)      91% ( 2)      16% ( 2)
largepage.collapse-mthp                   82% ( 1)      84% ( 1)      88% ( 1)
largepage.collapse-limits                 56% ( 2)      81% ( 1)      47% ( 2)
largepage.collapse-gup-fast               33% ( 4)      89% ( 6)       1% ( 4)
largepage.collapse-file                   68% ( 3)      91% ( 5)      21% ( 2)
largepage.collapse-pte-mapped             64% ( 2)      83% ( 3)      42% ( 2)
largepage.madv-collapse                   52% ( 2)      88% ( 3)      27% ( 2)
largepage.state-tracking                   5% ( 1)      54% ( 3)       0% ( 0)
largepage.anon-exclusive                  32% ( 1)      71% ( 3)      14% ( 1)
largepage.second-page-flags                8% ( 1)      86% ( 1)      21% ( 2)
largepage.nonatomic-flag-usage            13% ( 1)      84% ( 1)       6% ( 1)
largepage.mapcount-consistency            43% ( 2)      87% ( 2)      14% ( 1)
largepage.rmap-api                        29% ( 1)      62% ( 2)      24% ( 1)
largepage.pfn-alignment                   50% ( 1)      60% ( 2)       0% ( 0)
largepage.range-dedup                     51% ( 1)      80% ( 3)      20% ( 4)
largepage.pagecache-refs                  38% ( 1)      76% ( 1)      22% ( 1)
largepage.isize-mapping                   43% ( 2)      79% ( 3)      33% ( 2)
largepage.swapin                          59% ( 2)      87% ( 2)      90% ( 1)
largepage.migration                       56% ( 3)      91% ( 4)      18% ( 2)
largepage.unmap-pmd-mapped                33% ( 1)      72% ( 4)      17% ( 1)
largepage.hugetlb-vs-thp                  12% ( 4)      64% ( 7)      19% ( 2)
largepage.hstate-counters                 16% ( 3)      36% ( 1)      17% ( 2)
largepage.hugetlb-folio-state              7% ( 2)      78% ( 2)       8% ( 1)
largepage.hugetlb-alloc-paths             31% ( 4)      56% ( 5)      30% ( 2)
largepage.hugetlb-free                    31% ( 2)      81% ( 5)       7% ( 1)
largepage.hugetlb-surplus-adjust          32% ( 2)      86% ( 3)      43% ( 4)
largepage.hugetlb-demote                  20% ( 3)      84% ( 3)      49% ( 3)
largepage.hugetlb-reservation             54% ( 5)      73% ( 5)      29% ( 5)
largepage.hugetlb-subpool                 34% ( 2)      77% ( 1)      38% ( 2)
largepage.hugetlb-restore-reserve         49% ( 3)      82% ( 2)      26% ( 2)
largepage.hugetlb-cgroup                  37% ( 2)      77% ( 1)      18% ( 1)
largepage.hugetlb-fault-locks             37% ( 4)      70% ( 4)       4% ( 1)
largepage.hugetlb-fault-folio-lock        51% ( 2)      85% ( 2)      19% ( 1)
largepage.hugetlb-vma-lock                41% ( 2)      73% ( 4)      11% ( 1)
largepage.hugetlb-cow                     41% ( 2)      82% ( 2)      19% ( 3)
largepage.hugetlb-pagecache               41% ( 2)      73% ( 4)      14% ( 3)
largepage.hugetlb-walk                    33% ( 2)      78% ( 2)      35% ( 2)
largepage.hugetlb-pmd-share               32% ( 3)      87% ( 4)      29% ( 3)
largepage.hugetlb-pmd-unshare             57% ( 2)      94% ( 2)       8% ( 1)
largepage.hugetlb-type-usage              34% ( 4)      61% ( 3)      23% ( 4)
largepage.hugetlb-generic-paths           69% ( 3)      81% ( 2)      30% ( 3)
largepage.hugetlb-vmemmap                 58% ( 3)      82% ( 1)      31% ( 2)
largepage.hugetlb-migration               50% ( 2)      78% ( 3)      14% ( 1)
largepage.mf-returns                       0% ( 1)      67% ( 6)      32% ( 2)
largepage.mf-large-folio                  42% ( 3)      77% ( 3)       0% ( 0)
largepage.hwpoison-flags                   0% ( 0)      86% ( 3)       0% ( 0)
largepage.mf-hugetlb                      34% ( 1)      88% ( 2)      26% ( 1)
largepage.hwpoison-content-usage          53% ( 3)      83% ( 6)      10% ( 2)
largepage.unmap-poisoned                  45% ( 1)      84% ( 4)      11% ( 1)
largepage.mf-accounting                   61% ( 1)      78% ( 3)      22% ( 1)
largepage.change-new-alloc-site           83% ( 6)      82% ( 9)      59% ( 7)
largepage.change-split                    68% ( 3)      79% ( 5)      55% ( 6)
largepage.change-hugetlb-pool             71% ( 2)      77% ( 3)      34% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `largepage.deferred-split-alloc`, `largepage.collapse-file`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `largepage.kinds`, `largepage.anon-pmd-fault`, `largepage.anon-mthp-fault`, `largepage.pmd-cow`, `largepage.pmd-locking`, `largepage.split-preconditions`, `largepage.split-steps`, `largepage.split-state-propagation`, `largepage.collapse-gup-fast`, `largepage.anon-exclusive`, `largepage.second-page-flags`, `largepage.rmap-api`, `largepage.hugetlb-vs-thp`, `largepage.hugetlb-folio-state`, `largepage.hugetlb-free`, `largepage.hugetlb-vma-lock`, `largepage.hugetlb-cow`, `largepage.hugetlb-walk`, `largepage.hugetlb-pmd-share`.

## Questions reorganised

69 questions became 65, by subject: folio state, huge PMD entries, anonymous allocation, splitting,
deferred split, collapse, page cache and swap, the hugetlb pool, reservations, hugetlb faults and
page tables, memory failure. Merged: `second-page-flags` + `nonatomic-flag-usage` to
`second-page-flag-updates`; `anon-pmd-fault` + `change-new-alloc-site` to `anon-alloc-site`;
`split-steps` + `change-split` to `split-invariants`; `hugetlb-vs-thp` + `hugetlb-generic-paths` to
`hugetlb-in-generic-code`. Split: references, rmap and exclusivity left `pmd-split` for
`pmd-split-accounting`. Dropped: `hugetlb-folio-state`, an inventory readers A and C had right. The
step lists (collapse, the split) now ask for locks, revalidation and rollback.
