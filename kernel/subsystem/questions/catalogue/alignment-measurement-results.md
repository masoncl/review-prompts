# What the alignment measurement found

Three models were asked the 26 questions in `alignment-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C needed the fewest corrections
and reader B the most. The hand-written guide was never checked against
current sources, so differences between it and the built guide are expected
and are noted near the end.

The subject is small and old, and two of the three readers know nearly all of
what the hand-written guide says. What they get wrong is where the definitions
now live, how the page mask is typed, and the allocator and pageblock details
around the macros. Reader B is wrong about more, and wrong in ways that would
change a review.

## What all three readers got wrong

- **The generic macros are not defined in `include/linux/align.h`.** That file
  is one line, `#include <vdso/align.h>`. `ALIGN()`, `ALIGN_DOWN()`,
  `__ALIGN_MASK()`, `PTR_ALIGN()`, `PTR_ALIGN_DOWN()` and `IS_ALIGNED()` are
  in `include/vdso/align.h`, on top of `__ALIGN_KERNEL()` and
  `__ALIGN_KERNEL_MASK()` in `include/uapi/linux/const.h`. Every reader put
  them in the `linux/` header.
- **When the page mask is an int.** `include/vdso/page.h` defines `PAGE_MASK`
  as the signed `(~((1 << CONFIG_PAGE_SHIFT) - 1))` on every kernel without
  `CONFIG_64BIT`, so that it sign-extends over a 64-bit `phys_addr_t`. Readers
  A and C knew the trick and tied it to CONFIG_PHYS_ADDR_T_64BIT, which the
  header does not test. Reader B did not know it at all; see below.
- **No macro tests a pointer for alignment.** All three hedged. Nothing under
  `include/` does it; `IS_ALIGNED()` on a pointer does not compile,
  `PAGE_ALIGNED()` casts to unsigned long itself, and the one
  PTR_IS_ALIGNED in the tree is local to a driver.
- **Interfaces that need pageblock alignment.** `start_isolate_page_range()`
  aligns the range itself; `online_pages()` and `offline_pages()` check
  `pageblock_aligned()` on the start; a fixed CMA base that is not aligned is
  refused with -EINVAL, not aligned; hotplug ranges are checked against
  `memory_block_size_bytes()`. Each reader had at least one of these wrong.
- **Pageblock order and the buddy order.** The cap is `PAGE_BLOCK_MAX_ORDER`,
  the hugetlb case uses `HUGETLB_PAGE_ORDER` and not the PMD order, and the
  relation to `MAX_PAGE_ORDER` is an `#error` in `include/linux/mmzone.h`.
  Reader A called the cap PAGE_BLOCK_ORDER, reader B used `MAX_PAGE_ORDER`,
  reader C took a `MAYBE_BUILD_BUG_ON()` for a build-time check when it can
  fall back to a run-time one.
- **The minimum alignment constants.** `ARCH_SLAB_MINALIGN` has its own
  default and does not derive from `ARCH_KMALLOC_MINALIGN`; arm64 and riscv
  set `ARCH_KMALLOC_MINALIGN` to 8, below `ARCH_DMA_MINALIGN`, and select
  `CONFIG_DMA_BOUNCE_UNALIGNED_KMALLOC`; the kmalloc caches' real minimum is
  picked at boot by `__kmalloc_minalign()`. Reader A also offered
  CONFIG_ARCH_HAS_DMA_MINALIGN and arch_kmalloc_minalign(), neither of which
  exists.
- **Copies of the macros.** Every reader missed or misplaced some:
  `tools/include/linux/align.h`, `tools/include/linux/mm.h`,
  `tools/include/uapi/linux/const.h` (checked by
  `tools/perf/check-headers.sh`), the pageblock macros in
  `tools/testing/memblock/linux/mmzone.h` and
  `tools/testing/vma/linux/mmzone.h`, a private `ALIGN()` in
  `scripts/dtc/dtc.h`, and Rust's `page_align()` in `rust/kernel/page.rs`,
  which returns `None` on overflow where the C macro wraps.
- **Unaligned access helpers** (outside the guide's triggers). All three said
  `get_unaligned()` reads through a packed structure. `__get_unaligned_t()`
  and `__put_unaligned_t()` in `include/vdso/unaligned.h` use
  `__builtin_memcpy()`, and nothing in the header tests
  `CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS`.

## What readers A and B got wrong

- `PAGE_SIZE` and `PAGE_MASK` were placed in include/asm-generic/page.h,
  which does not exist. They are in `include/vdso/page.h`.
- Callers that walk a zone by pageblock: only `fast_isolate_around()` clamps
  both ends to the zone. `isolate_migratepages_range()` clamps the start to
  the zone and each end to the caller's end. `pageblock_pfn_to_page()` checks
  the first and last page frame only, so a block with a hole can pass.
- Whether this tree has an annotation for structure members a device writes
  by DMA: reader A was unsure, reader B said there is none. There is,
  `__dma_from_device_group_begin()` and `__dma_from_device_group_end()`.

## What reader B got wrong as well

These are the ones that would change a verdict.

- **`pageblock_align()` on an exclusive end, backwards.** It called
  `pageblock_align(end_pfn)` on an exclusive end unsafe. That is the correct
  form and is what `start_isolate_page_range()` does; the unsafe one is
  `pageblock_end_pfn(end_pfn)`, which moves an aligned end to the next block.
  It also said `start_isolate_page_range()` requires aligned input.
- **`phys & PAGE_MASK` called unsafe on 32-bit.** It said the definition is
  the same everywhere and zero-extends. Only the open-coded
  `~(PAGE_SIZE - 1)` does that.
- **kmalloc alignment.** Sizes that are not a power of two "aligned to the
  bucket size" (only the largest power-of-two divisor is guaranteed), and the
  guarantee "only assured with debugging disabled" (it holds: the alignment is
  the cache's `align` and the red zone is padded to it).
- **`kfree()` "handles memory from any allocator".** It warns on a page that
  is not a large kmalloc.
- **`kmalloc_size_roundup()` offered as the fix for DMA alignment.** It is
  not.
- **A 32-bit value with a 64-bit alignment** gives "a small mask". The
  alignment is cast to the value's type first, so it becomes 0, the mask is
  all ones and the result is 0.
- `round_up()` and `roundup()` said to evaluate their arguments several
  times; only `ALIGN()` and `ALIGN_DOWN()` do. `round_up()` and the rest
  placed in `kernel.h`; they are in `include/linux/math.h` and
  `include/linux/log2.h`. `PAGE_ALIGN()` placed in `include/vdso/page.h`; it
  is in `include/linux/mm.h`.
- `pageblock_order` said to be a variable whenever hugetlb and THP are both
  set (only under `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`), and
  `set_pageblock_order()` placed in `mm/page_alloc.c` (it is in
  `mm/mm_init.c`).
- No in-tree guard against `ALIGN()` wrapping was known. `do_mmap()`,
  `do_mprotect_pkey()` and the mseal system call all check for it.

## What the readers already knew

Which way each macro rounds and that an aligned input is returned unchanged;
that the alignment must be a power of two, that nothing checks it, and that
`roundup()` and `rounddown()` take any multiple; what `PAGE_ALIGN()`,
`PAGE_ALIGN_DOWN()` and `PAGE_ALIGNED()` expand to (readers A and C); the
address and page frame conversions in `include/linux/pfn.h`, including that
`PFN_ALIGN()` returns a byte address and truncates; the four pageblock
macros and the table of what they return on and just after a boundary (all
three); that `pageblock_end_pfn()` is exclusive (all three); counting pages in
a byte range with the offset added in; packed structures.

That list is most of the hand-written guide.

## Where the hand-written guide is stale

`alignment.md` sends the reader to `include/linux/align.h` for the macros;
they are in `include/vdso/align.h`. Its other statements hold on this tree:
the page helpers are in `include/linux/mm.h`, the pageblock macros are spelled
as it quotes them in `include/linux/pageblock-flags.h`, and the `kmalloc()`
statement matches the comment above `kmalloc()`. Its cross-reference to a
section heading in `mm-alloc.md` names a heading that a built guide will not
keep. More to the point, two thirds of its words restate macro definitions
that every reader measured here already gives correctly, and it says nothing
about operand types, wrapping, the page mask, how `pageblock_order` is
defined, or the copies under `tools/`.

## What was left out of the build set, and why

Ten questions were kept, with the same text as in the measurement set, and
their budgets add up to 520 words. The hand-written guide is 401 words, so the
built guide is sized to 600 words, the floor for a guide whose hand-written
original is shorter, and no question is given fewer than 40: a first build at
the hand-written guide's size, with nine questions of 25 to 45 words each,
came out as fragments that meant nothing without the question beside them
("Unsigned: 0.", "Other sizes: largest power-of-two divisor."). Most of the
room the larger size gave went to the nine budgets. The rest went to
`align.pageblock-requirements`, the next in line: every reader had wrong at
least one of which interfaces round a range of page frames out to pageblocks
themselves and which refuse one that is not aligned, and a reviewer who has it
backwards asks one caller for alignment it does not owe and lets through
another that does owe it. Two of the ten, `align.core-files` and
`align.overflow`, had a clause added in both files after the measurement, to
ask for every header as a full path and to ask about a signed operand under
the compiler options the kernel is built with as well as an unsigned one; what
they ask is otherwise the same.

- `align.macro-family`, `align.power-of-two`, `align.round-up-family`,
  `align.page-helpers`, `align.pfn-conversions`, `align.unit-mismatch`,
  `align.pageblock-helpers`, `align.range-to-pages`: the readers answer them.
  The locations that readers had wrong in them are covered by
  `align.core-files`.
- `align.pointer-forms`: every reader hedged, but the mistake does not
  compile.
- `align.minalign-constants`: all three were wrong and it matters for DMA, but
  it is about mapping `kmalloc()` memory for a device, not about a use of the
  macros this guide is loaded for. It belongs with the DMA mapping material.
- `align.pageblock-zone-clamp`, `align.pageblock-vs-max-order`: real,
  relevance 3, confined to `mm/compaction.c` and `mm/page_alloc.c`; no room,
  and each would be the next to come back if the guide were allowed more
  words. The cap on `pageblock_order` is asked by `align.pageblock-order`.
- `align.other-allocators`: a table of what each allocator gives is the
  allocator guide's subject.
- `align.unaligned-access`, `align.packed-aligned`, `align.cacheline-attrs`:
  measured because they share the word. The guide's triggers are the rounding
  and pageblock macros, and these would need a guide of their own; the results
  above say what it would have to correct.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           45        25%      9      6   6.12 to 6.16
reader B           63        67%      1     24   6.10 to 6.12
reader C           30        15%     15      1   6.12 to 6.19

question                          reader A      reader B      reader C
align.core-files                  24% ( 6)      41% ( 8)      15% ( 3)
align.macro-family                12% ( 3)      61% ( 2)       0% ( 1)
align.power-of-two                 6% ( 0)      68% ( 1)       8% ( 1)
align.result-type                 12% ( 1)      79% ( 2)       0% ( 0)
align.overflow                     6% ( 1)      79% ( 1)      34% ( 1)
align.round-up-family              5% ( 1)      79% ( 1)       0% ( 0)
align.pointer-forms               32% ( 1)      68% ( 1)      34% ( 1)
align.page-helpers                 0% ( 0)      83% ( 3)       0% ( 0)
align.page-mask                   16% ( 1)      65% ( 1)       7% ( 1)
align.pfn-conversions             15% ( 1)      59% ( 1)       9% ( 1)
align.unit-mismatch               16% ( 1)      58% ( 1)      24% ( 1)
align.range-to-pages              29% ( 1)      34% ( 1)      15% ( 1)
align.pageblock-order             11% ( 1)      71% ( 5)       0% ( 0)
align.pageblock-helpers           40% ( 2)      14% ( 1)       0% ( 0)
align.pageblock-end-usage          0% ( 0)      73% ( 4)       5% ( 1)
align.pageblock-zone-clamp        56% ( 1)      79% ( 3)       0% ( 0)
align.pageblock-requirements      36% ( 1)      87% ( 4)      19% ( 2)
align.pageblock-vs-max-order      42% ( 1)      78% ( 4)      38% ( 3)
align.kmalloc-guarantee           21% ( 1)      65% ( 2)      15% ( 1)
align.minalign-constants          33% ( 3)      84% ( 3)      20% ( 2)
align.page-aligned-origin         19% ( 1)      71% ( 2)      20% ( 1)
align.other-allocators            20% ( 3)      56% ( 4)      27% ( 2)
align.unaligned-access            44% ( 2)      90% ( 1)      17% ( 1)
align.packed-aligned              21% ( 1)      56% ( 1)       0% ( 0)
align.cacheline-attrs             57% ( 2)      83% ( 1)      32% ( 2)
align.copies                      80% ( 9)      82% ( 5)      51% ( 4)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `align.macro-family`, `align.power-of-two`, `align.page-helpers`, `align.pfn-conversions`, `align.minalign-constants`.

## Questions reorganised

Grouped by subject: generic helpers, page helpers, pageblocks, allocator alignment, after the overview,
the model gaps and the file table. 17 questions became 16.
Merged: `align.macro-family` and `align.power-of-two` into `align.generic-contract` (what an aligned
input gives back, what the alignment argument must be, whether anything checks it).
`align.copies` moved into generic helpers and asks what a change must keep in step, not for a list
of files. `align.page-helpers`, `align.pfn-conversions`, `align.pageblock-order`,
`align.pageblock-requirements` and `align.minalign-constants` were reworded as contracts (argument
kinds, who does the aligning) and no longer ask what a macro expands to. Nothing was dropped.
