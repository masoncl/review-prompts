# What the mm-folio measurement found

Two models were asked the 60 questions in `mm-folio-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-folio.md` holds the questions it does. The readers are labelled A (the
more current, which assumed 6.16 to 6.18) and B (a few releases older). Which
models they were does not matter here.

## How it differs from mm-vma

For VMAs the readers already knew the concepts and were wrong about what had
moved. For folios that is true of reader A only. Reader B is wrong about
fundamentals, so there is very little that every reader already knows, and the
build set could not be chosen by dropping what is known. It was chosen by
importance, within the size of the hand-written guide.

## What reader A got wrong: what has moved

- **Files.** It said in five answers that `mm/folio.c` does not exist and that
  the release path, the per-CPU LRU batches and `folio_mark_accessed()` are in
  `mm/swap.c`. In this tree it is the other way round, and `pagevec.h` is
  `folio_batch.h`.
- **The head pointer.** It read `page->compound_head`. The field is
  `compound_info`, read by `_compound_head()`, and with the hugetlb vmemmap
  optimisation it is not a simple pointer. `nth_page()` and `page_mapped()` no
  longer exist.
- **Second-page flags** are declared with `FOLIO_FLAG(..., FOLIO_SECOND_PAGE)`;
  nothing uses the `PF_SECOND` policy. Hugetlb folios have a page type and are
  still mapped. The page-pool descriptor is `struct netmem_desc`.
- **The swap cache** is a swap table under the swap cluster lock, not an
  xarray under `xa_lock`.
- **Which folios have a pincount**: `folio_has_pincount()` is any large folio
  on 64-bit and order above one on 32-bit.
- **Per-mm mapcount tracking**: when the shared bit is set and cleared, and
  that it depends on `CONFIG_MM_ID`.
- **The LRU batches**: a queued folio keeps `PG_lru` as it was; the move
  function does the test-and-clear; draining `lru_add` frees dead folios by
  freezing the count at one; `lru_activate` exists only on SMP.
- **Lazyfree**: `PGLAZYFREED` is counted in reclaim after the freeze, not in
  the unmap; only a dirty folio outside a droppable mapping is marked
  swap-backed again.
- **Details of many functions**: the order of steps in `__folio_put()`;
  `filemap_alloc_folio()` takes a memory policy; `xas_try_split()` when adding
  over a larger shadow entry; `__remove_mapping()` freezes at one plus the
  number of pages; invalidation returns busy only when the release fails or the
  folio is dirty; truncation can leave a dirty large folio it could not split;
  `mapping_set_folio_min_order()` also sets the maximum.

## What reader B got wrong as well: fundamentals

- The page cache and the swap cache hold "one reference in total" on a large
  folio. They hold one per page.
- Page table mappings "take no reference". Each present entry is paired with
  one.
- The folio lock is ordered above the mmap lock. It nests inside it.
- The order is a `u8` field and no page count is cached. The order is the low
  byte of the first tail's flags word, and `_nr_pages` caches the count under
  some configurations.
- `CONFIG_NO_PAGE_MAPCOUNT` removes the per-page fields. It stops maintaining
  them.
- Invented or departed names throughout: `folio_try_get_rcu()`, `FGP_ENTRY`,
  `FGP_HUGE`, `__split_huge_page()`, `PAGEFLAG_ATOMIC`, `_folio_order`,
  `_folio_nr_pages`.
- `lruvec_stat_mod_folio()` multiplies by the number of pages. It passes the
  value through; only the add and sub helpers multiply.
- `filemap_dirty_folio()` as the entry point for marking dirty. It is one
  implementation of the hook `folio_mark_dirty()` calls.

## What both already knew

The files and the entry points for most jobs (apart from the `mm/swap.c`
rename), the lockless lookup's outline, and, for reader A, the expected
reference holders, the lookup API's return convention, multi-index entries,
how to add a page flag and how statistics are counted.

## Left out of the build set

For space, not because the readers know them: what a folio is, the fields by
purpose, order and size on its own, `folio_page()`, `kmap_local_folio()`,
exact-count comparisons, locking after GUP, lock state on error paths,
`folio_end_read()`, the workingset hook on cache nodes, the residency system
calls, uncached buffered I/O, `folio_mark_accessed()`, per-section metadata
and the page-based wrappers. If the built guide comes in under its size, these
are the candidates to add back, `folio_end_read()` and locking after GUP
first.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too, so it overstates reader
B's gap; the corrections are what count.

```
reader A: 98 corrections, 32% rewritten on average
reader B: 150 corrections, 77% rewritten on average

question                            reader A        reader B
folio.what-it-represents             15% ( 3)        80% ( 6)
folio.fields                          7% ( 1)        57% ( 3)
folio.tail-overlays                  53% ( 4)        70% ( 1)
folio.order-and-size                 17% ( 1)        87% ( 1)
folio.flags-word                     28% ( 1)        77% ( 5)
folio.page-types                     33% ( 1)        90% ( 4)
folio.not-folios                     39% ( 1)        76% ( 5)
folio.page-to-folio                  34% ( 3)        75% ( 4)
folio.folio-page                      4% ( 1)        66% ( 2)
folio.pfn-validity                    8% ( 1)        82% ( 1)
folio.kmap                           25% ( 2)        75% ( 1)
folio.alloc                          45% ( 5)        71% ( 5)
folio.free                           65% ( 3)        74% ( 3)
folio.zone-device                    68% ( 3)        85% ( 3)
folio.refcount-holders                4% ( 3)        83% ( 4)
folio.expected-ref-count             47% ( 2)        85% ( 3)
folio.ref-freeze                     17% ( 1)        77% ( 3)
folio.try-get                        20% ( 1)        66% ( 2)
folio.pincount                       26% ( 1)        77% ( 4)
folio.refcount-as-state              15% ( 1)        89% ( 1)
folio.mapcount-fields                21% ( 1)        76% ( 6)
folio.mm-id-tracking                 57% ( 3)        95% ( 2)
folio.mapcount-vs-refcount           30% ( 2)        79% ( 2)
folio.mapped-tests                   64% ( 3)        79% ( 2)
folio.lock                           23% ( 2)        70% ( 3)
folio.recheck-after-lock             28% ( 1)        85% ( 3)
folio.lock-after-gup                 42% ( 1)        92% ( 2)
folio.lock-at-error-labels           30% ( 1)        84% ( 3)
folio.flag-ownership                  6% ( 3)        29% ( 9)
folio.flag-tests-need-ref            32% ( 1)        77% ( 1)
folio.uptodate                       30% ( 1)        79% ( 1)
folio.mapping-field                  20% ( 2)        84% ( 1)
folio.private                        16% ( 1)        91% ( 1)
folio.pagecache-structure            21% ( 1)        79% ( 2)
folio.lookup-api                     31% ( 1)        94% ( 1)
folio.lockless-lookup                22% ( 1)        81% ( 1)
folio.batch-lookups                  35% ( 2)        56% ( 1)
folio.xas-multi-index                30% ( 1)        88% ( 1)
folio.add-to-cache                   24% ( 1)        71% ( 3)
folio.remove-from-cache              35% ( 2)        75% ( 1)
folio.large-folio-support            43% ( 1)        84% ( 1)
folio.truncate-vs-invalidate         25% ( 2)        90% ( 1)
folio.mapping-set-update             49% ( 1)        90% ( 1)
folio.info-disclosure                18% ( 1)        88% ( 1)
folio.dropbehind                     46% ( 1)        86% ( 1)
folio.lru-batching                   50% ( 3)        78% ( 6)
folio.lru-drain                      61% ( 1)        79% ( 3)
folio.lru-flags                      37% ( 1)        78% ( 5)
folio.lazyfree                       50% ( 3)        82% ( 4)
folio.mark-accessed                  51% ( 2)        86% ( 3)
folio.speculative-access             26% ( 1)        87% ( 1)
folio.pfn-step                        6% ( 0)        88% ( 1)
folio.order-without-ref              13% ( 1)        87% ( 2)
folio.sections                       79% ( 2)        85% ( 2)
folio.layout-change                  46% ( 1)        90% ( 2)
folio.adding-a-flag                  56% ( 1)        84% ( 2)
folio.compat-wrappers                45% ( 1)        81% ( 1)
folio.stat-accounting                44% ( 1)        91% ( 1)
folio.core-files                      1% ( 3)         4% ( 1)
folio.entry-points                    7% ( 1)        17% ( 4)
```

## Questions reorganised

Subjects now: pages, heads and tails; converting between pages and folios; references and mapcounts;
mapping and private; the folio lock; flags; the LRU; PFN scanners; page cache lookup; changing what
is cached; allocating and freeing. 62 questions became 57. Merged: `folio.order-and-size`,
`folio.order-without-ref` and `folio.pfn-step` into `folio.order-reads`; `folio.ref-freeze` and
`folio.refcount-as-state` into `folio.ref-freeze-exact`. Dropped: `folio.what-it-represents` (the
overview asks it) and `folio.fields` (an inventory that opening the header shows). The questions
under "Changing the implementation" went to the subject each belongs to. `folio.sections` no longer
presumes a stepping helper, since the one the readers named is gone.
