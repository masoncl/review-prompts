# What the mm-vma measurement found

Three models were asked the 116 questions in `mm-vma-measurement-116.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-vma.md` holds the questions it does. The table is the output of `kernel/scripts/compare-runs.py`:
the share of each from-memory answer the checker rewrote, with the number of
corrections in brackets.

## What the readers already knew

The concepts and the architecture, nearly all of it: that the mmap write lock
alone does not exclude per-VMA readers, how long a VMA pointer is good under
each lock, the lock inventory, the two lookups, that anonymous means no
operations table and that a private mapping of the zero device keeps its file,
that the modify functions return an error pointer and never NULL, the shapes a
merge takes, the state of the VMA when an mmap hook runs. About nine names in
ten that a reader offered exist in the tree.

## What they got wrong

- **Names and layouts that have moved.** Flags as a bitmap (`vma_flags_t`, the
  `VMA_*_BIT` numbers, `vma_set_flags()`, `vma_flags_reset_once()`); the second,
  anonymous page offset; the reverse-map tree helpers (`mapping_rmap_tree_*`,
  `anon_rmap_tree_*`, `unlink_file_vma_batch_*`); the per-VMA lock's constants
  and functions; the phases of the mmap path and its newer hook; which file a
  function is in; who calls the notifications.
- **Facts that would change a verdict**, about twenty. Per-VMA-locked
  `MADV_DONTNEED` can free a page table (two readers said it cannot). A hook
  that replaces the file in `mmap_prepare` must own a reference (readers said
  the opposite). `vma_assert_locked()` fires under the mmap read lock; the
  either-lock assertion is `vma_assert_stabilised()`. `close()` is never called
  for a VMA a merge removes. `free_pgtables()` runs after the lock is
  downgraded. The map-count check is in `split_vma()`, not `__split_vma()`. A
  failed map-over-existing completes the unmap once the PTEs are cleared. A
  failed fork leaves no placeholder entries.
- **Blanks.** Readers said plainly that they did not recognise `vma_flags_t`,
  `vma_set_anon_pgoff()`, `unuse_mm()`, the detach helper, or the layout of the
  userland test build.

## The readers differ in kind

The most current reader (reader A below, which assumed 6.15 to 7.0) knew
the most, and carried confident facts that were true for a few releases and
have since changed again: `XA_ZERO_ENTRY` markers after a failed fork,
`VMA_LOCK_OFFSET` and `__vma_enter_locked()`, `hugetlb_free_pgd_range()`, smaps
under the mmap lock. The oldest (reader C, 6.6 to 6.16) had whole
mechanisms out of date, such as the per-VMA lock as an rwsem, and avoided
reader A's mistakes only by never having learned those facts. All three were weak
on the second page offset, how fork copies the tree, anonymous VMAs that keep a
file, which flags merging ignores, and the userland tests. A guide has to cover
the union.

## The numbers

The readers are labelled A to C from the most current to the oldest. Which
models they were does not matter here; what matters is that readers of
different ages are wrong about different things.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A          185        20%     47     12   6.15 to 7.0
reader-B          221        33%     24     46   6.12 to 6.17
reader-C          215        65%      5    102   6.6 to 6.16

question                           reader-A      reader-B      reader-C   verdict
vma.what-it-represents             23% ( 1)      14% ( 1)      28% ( 1)   middling
vma.fields                         19% ( 2)      21% ( 4)      34% ( 6)   middling
vma.field-stability                16% ( 1)      24% ( 2)      78% ( 3)   weak: reader-C
vma.page-offset                    64% ( 3)      60% ( 4)      79% ( 3)   all weak
vma.tree                            5% ( 1)      22% ( 1)       0% ( 0)   middling
vma.lookup-api                      0% ( 0)       0% ( 0)       0% ( 0)   all fair: drop, or shrink to a pointer
vma.iterator                        1% ( 1)      26% ( 1)      49% ( 2)   weak: reader-C
vma.gaps                            7% ( 1)       0% ( 0)      68% ( 1)   weak: reader-C
vma.map-count-limit                25% ( 1)      81% ( 2)      78% ( 1)   weak: reader-B, reader-C
vma.alloc-free                      0% ( 0)      18% ( 1)      52% ( 3)   weak: reader-C
vma.rcu-slab                        2% ( 1)      54% ( 1)      57% ( 1)   weak: reader-B, reader-C
vma.attached-detached              15% ( 4)      22% ( 1)      55% ( 1)   weak: reader-C
vma.visibility                     27% ( 1)      26% ( 1)      74% ( 5)   weak: reader-C
vma.creators                       16% ( 1)      13% ( 2)      39% ( 1)   middling
vma.mmap-path                       3% ( 1)      43% ( 3)      78% ( 1)   weak: reader-B, reader-C
vma.mmap-replaces                   0% ( 0)      62% ( 2)      84% ( 2)   weak: reader-B, reader-C
vma.fork-copy                      18% ( 4)      47% ( 2)      80% ( 1)   weak: reader-B, reader-C
vma.stack                          30% ( 1)      17% ( 2)      70% ( 2)   weak: reader-C
vma.special-mappings               16% ( 1)      40% ( 1)      68% ( 1)   weak: reader-B, reader-C
vma.operations                     11% ( 4)      30% ( 5)      52% ( 4)   weak: reader-C
vma.modify-family                   6% ( 2)      27% ( 2)      61% ( 2)   weak: reader-C
vma.munmap-phases                   9% ( 2)      24% ( 2)      84% ( 2)   weak: reader-C
vma.exit-teardown                  41% ( 1)      11% ( 1)      80% ( 1)   weak: reader-A, reader-C
vma.move                           34% ( 1)      15% ( 1)      58% ( 1)   weak: reader-C
vma.anon-test                       0% ( 1)      12% ( 1)      63% ( 1)   weak: reader-C
vma.anon-kinds                     12% ( 2)       5% ( 2)      49% ( 2)   weak: reader-C
vma.anon-with-file                 44% ( 3)      70% ( 3)      73% ( 3)   all weak
vma.kind-flags                     22% ( 3)      47% ( 2)      85% ( 3)   weak: reader-B, reader-C
vma.flag-groups                     8% ( 1)      24% ( 1)      25% ( 1)   middling
vma.two-flag-apis                  16% ( 2)      94% ( 2)      90% ( 2)   weak: reader-B, reader-C
vma.page-prot                      11% ( 1)      40% ( 2)      75% ( 3)   weak: reader-B, reader-C
vma.file-rmap                      18% ( 3)      35% ( 2)      79% ( 2)   weak: reader-C
vma.anon-rmap                      18% ( 3)      43% ( 2)      66% ( 1)   weak: reader-B, reader-C
vma.page-tables                    26% ( 4)      52% ( 1)      81% ( 1)   weak: reader-B, reader-C
vma.vm-ops                         17% ( 2)      41% ( 4)      69% ( 1)   weak: reader-B, reader-C
vma.other-attachments              28% ( 2)      47% ( 1)      67% ( 1)   weak: reader-B, reader-C
vma.commit-check-charges           14% ( 1)      42% ( 1)      87% ( 1)   weak: reader-B, reader-C
vma.account-flag                   54% ( 3)       3% ( 1)      86% ( 2)   weak: reader-A, reader-C
vma.vm-stat                        32% ( 1)      50% ( 3)      88% ( 1)   weak: reader-B, reader-C
vma.lock-inventory                  1% ( 1)      10% ( 2)      12% ( 3)   all fair: drop, or shrink to a pointer
vma.per-vma-lock-mechanism         30% ( 2)      39% ( 3)      75% ( 2)   weak: reader-C
vma.mmap-write-lock-effect          0% ( 0)       0% ( 0)      73% ( 1)   weak: reader-C
vma.vma-write-lock-effect          15% ( 1)      15% ( 0)      67% ( 1)   weak: reader-C
vma.vma-lock-only-operations       28% ( 4)      51% ( 3)      84% ( 3)   weak: reader-B, reader-C
vma.lock-modes                      4% ( 2)      12% ( 3)      48% ( 4)   weak: reader-C
vma.no-per-vma-lock-config         45% ( 2)      55% ( 2)      89% ( 1)   all weak
vma.pointer-validity               11% ( 1)      10% ( 2)      76% ( 1)   weak: reader-C
vma.per-vma-lock-api               32% ( 1)      27% ( 1)      71% ( 2)   weak: reader-C
vma.rcu-lookup-steps               18% ( 2)      47% ( 4)      75% ( 1)   weak: reader-B, reader-C
vma.rcu-release-touches-mm         26% ( 1)      15% ( 2)      86% ( 1)   weak: reader-C
vma.rcu-foreign-mm                  9% ( 1)      31% ( 1)      82% ( 1)   weak: reader-C
vma.tree-state-rcu                 21% ( 1)      36% ( 1)      80% ( 1)   weak: reader-C
vma.killable-lock-return           63% ( 1)      54% ( 1)      71% ( 2)   all weak
vma.unstable-mm-mark                9% ( 1)      49% ( 3)      65% ( 2)   weak: reader-B, reader-C
vma.failed-fork-tree               69% ( 1)      63% ( 5)      80% ( 3)   all weak
vma.other-mm-usage                 47% ( 2)      55% ( 4)      18% ( 3)   weak: reader-A, reader-B
vma.file-pointer-uses              14% ( 3)       3% ( 0)      40% ( 2)   weak: reader-C
vma.anon-vs-file-usage             18% ( 1)       4% ( 3)      77% ( 1)   weak: reader-C
vma.rmap-tree-key                  58% ( 2)      47% ( 2)      70% ( 1)   all weak
vma.assertion-accepts              16% ( 1)      34% ( 2)      75% ( 4)   weak: reader-C
vma.assertion-choice               18% ( 1)      54% ( 4)      84% ( 2)   weak: reader-B, reader-C
vma.flags-helpers                  27% ( 2)      40% ( 4)      67% ( 4)   weak: reader-B, reader-C
vma.flags-no-write-lock             0% ( 1)      89% ( 1)      88% ( 1)   weak: reader-B, reader-C
vma.flags-replace-idiom            53% ( 1)      51% ( 2)      66% ( 1)   all weak
vma.flags-usage                    19% ( 1)      47% ( 1)      69% ( 2)   weak: reader-B, reader-C
vma.fork-cleared-flags             31% ( 1)      24% ( 1)      73% ( 3)   weak: reader-C
vma.fork-flag-tests                21% ( 1)      45% ( 1)      80% ( 1)   weak: reader-B, reader-C
vma.two-mmap-hooks                  1% ( 1)      26% ( 1)      29% ( 2)   middling
vma.hook-vma-state                 23% ( 1)       3% ( 1)      59% ( 1)   weak: reader-C
vma.hook-may-set                    9% ( 2)      23% ( 2)      57% ( 2)   weak: reader-C
vma.hook-failure                   15% ( 2)       0% ( 1)      70% ( 1)   weak: reader-C
vma.open-close-pairing             13% ( 1)      27% ( 1)      57% ( 2)   weak: reader-C
vma.may-split-hook                 27% ( 1)      25% ( 1)      18% ( 1)   middling
vma.mmap-file-refs                 32% ( 1)      36% ( 1)      64% ( 1)   weak: reader-C
vma.mmap-file-swap-hooks           30% ( 1)      33% ( 3)      59% ( 5)   weak: reader-C
vma.mmap-file-swap-duty            38% ( 1)      18% ( 1)      31% ( 1)   middling
vma.mmap-file-usage                37% ( 2)      24% ( 1)      51% ( 1)   weak: reader-C
vma.modify-returns                  0% ( 0)       6% ( 2)      68% ( 2)   weak: reader-C
vma.merge-returns                  21% ( 1)      46% ( 1)      66% ( 2)   weak: reader-B, reader-C
vma.merge-frees-input              32% ( 1)      37% ( 1)      16% ( 1)   middling
vma.merge-state-on-failure         17% ( 1)      19% ( 1)      91% ( 2)   weak: reader-C
vma.modify-cannot-fail             10% ( 1)      55% ( 1)      84% ( 1)   weak: reader-B, reader-C
vma.iterating-while-modifying       3% ( 1)      40% ( 1)      80% ( 1)   weak: reader-B, reader-C
vma.merge-result-usage             14% ( 1)      25% ( 2)      61% ( 1)   weak: reader-C
vma.merge-flag-compare             43% ( 6)      77% ( 4)      90% ( 3)   all weak
vma.flags-before-merge             22% ( 2)      50% ( 2)      87% ( 3)   weak: reader-B, reader-C
vma.commit-accounting-usage        33% ( 1)      30% ( 2)      81% ( 5)   weak: reader-C
vma.vm-account-preservation        17% ( 2)      47% ( 3)      62% ( 3)   weak: reader-B, reader-C
vma.tree-invariants                24% ( 4)      31% ( 5)      61% ( 2)   weak: reader-C
vma.preallocation                  39% ( 4)      16% ( 1)      77% ( 2)   weak: reader-C
vma.store-helpers                  26% ( 2)      21% ( 2)      59% ( 3)   weak: reader-C
vma.range-change-functions         11% ( 1)      66% ( 2)      54% ( 4)   weak: reader-B, reader-C
vma.split-merge-window             11% ( 3)      16% ( 1)      70% ( 4)   weak: reader-C
vma.why-rmap-reinsert              24% ( 2)      33% ( 1)      67% ( 1)   weak: reader-C
vma.window-lock-variant            12% ( 0)      35% ( 1)      92% ( 2)   weak: reader-C
vma.window-not-excluded            27% ( 1)      14% ( 1)      78% ( 1)   weak: reader-C
vma.range-change-usage             39% ( 1)      24% ( 1)      54% ( 1)   weak: reader-C
vma.stack-growers-exception        13% ( 1)      33% ( 1)      77% ( 1)   weak: reader-C
vma.merge-uprobe-side-effect       21% ( 0)      32% ( 1)      72% ( 1)   weak: reader-C
vma.merge-conditions               21% ( 3)      35% ( 6)      84% ( 2)   weak: reader-C
vma.merge-cases                     6% ( 1)       2% ( 1)      69% ( 1)   weak: reader-C
vma.merge-state                    12% ( 2)      46% ( 3)      74% ( 1)   weak: reader-B, reader-C
vma.merge-anon-propagation          3% ( 1)       0% ( 0)       0% ( 0)   all fair: drop, or shrink to a pointer
vma.merge-fork-test-side           14% ( 0)      78% ( 2)      82% ( 1)   weak: reader-B, reader-C
vma.close-hook-and-merge           21% ( 0)      45% ( 2)      13% ( 0)   weak: reader-B
vma.read-lock-order                 5% ( 2)      19% ( 3)      71% ( 2)   weak: reader-C
vma.lock-ordering                  21% ( 3)      45% ( 1)      92% ( 1)   weak: reader-B, reader-C
vma.detach-waits                    4% ( 1)      53% ( 1)      87% ( 2)   weak: reader-B, reader-C
vma.lock-refcount-balance          18% ( 1)      71% ( 2)      63% ( 2)   weak: reader-B, reader-C
vma.mmap-unwind                    15% ( 4)      18% ( 7)      78% ( 3)   weak: reader-C
vma.split-failure                  11% ( 2)       2% ( 1)      79% ( 1)   weak: reader-C
vma.munmap-failure                 27% ( 1)      44% ( 2)      88% ( 2)   weak: reader-B, reader-C
vma.core-notifications              7% ( 5)      31% ( 7)      51% ( 5)   weak: reader-C
vma.userland-tests                 47% ( 1)      56% ( 2)      87% ( 1)   all weak
vma.nommu                          22% ( 1)      30% ( 1)      76% ( 1)   weak: reader-C
vma.config-variants                34% ( 2)      36% ( 2)      75% ( 3)   weak: reader-C

Rewritten is word-level and counts rewording, so read the corrections in each run-report.md
before trusting a number. (n) is how many corrections the checker listed.
```

## Questions reorganised

By subject now, one builder call each: flags; per-VMA locks and lookups; locks and page tables;
mapping a region; callbacks; merge and modify; range changes and the tree; fork and foreign address
spaces; overcommit accounting. Nothing merged or dropped: 41 questions before and after.
`vma.userland-tests` moved beside the file tables under "Finding your way". Questions that asked for
fields, constants or lists of functions (`vma.per-vma-lock-parts`, `vma.mmap-phases`,
`vma.merge-conditions`, `vma.merge-state-on-failure`, `vma.mmap-unwind`, `vma.range-change-sequence`)
now ask what a caller must do or what reuse is unsafe; `vma.open-close-pairing` no longer repeats
what `vma.vm-ops` tabulates.
