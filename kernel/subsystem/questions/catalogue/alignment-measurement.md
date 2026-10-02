# Questions: Alignment Helpers (measurement set)

- guide: alignment.md
- title: Alignment Helpers

A wide set of questions about the alignment helpers, used to measure what a
model already knows before deciding what the built guide should spend its
words on. The hand-written guide it will replace is 401 words and covers four
things: the generic round-up, round-down and test macros, the page-sized
forms, the pageblock forms that work on page frame numbers, and what alignment
the allocators give. It is loaded when a diff uses one of those macros. The
last part of this file asks about neighbouring subjects (unaligned access,
packed structures, cache line annotations) that the guide is not loaded for;
they are measured, not built. Format: `../../../docs/subsystem-questions.md`.

# The generic helpers

## align.core-files: Core files

- section: Finding your way
- relevance: 4 - the definitions are spread over several headers and some have moved
- words: 90

Which headers define the generic alignment macros (round up, round down, test,
the pointer forms), the primitives they expand to, the page-sized forms, the
page size and page mask, the conversions between byte addresses and page frame
numbers, the pageblock forms, and the macros that round to a power of two or to
an arbitrary multiple? A table. Write every header as its full path from the
top of the tree. Start from `include/linux/align.h`.

## align.macro-family: Generic macro family

- section: Generic helpers
- relevance: 4 - the direction and the already-aligned case are what get misread
- words: 80

What does each macro in the generic alignment header compute: the round-up
form, the round-down form, the form that takes a mask, the pointer forms and
the test? What does each return for an input that is already aligned? Start
from `ALIGN()` and `ALIGN_DOWN()`.

## align.power-of-two: Alignment argument requirement

- section: Generic helpers
- relevance: 5 - a wrong argument gives a plausible wrong number and nothing warns
- words: 70

What must the alignment argument of `ALIGN()`, `ALIGN_DOWN()` and
`IS_ALIGNED()` be for the result to be right, and does anything check it at
build time or at run time? What do the macros compute when the requirement is
not met, and which macros round to an arbitrary multiple instead?

## align.result-type: Operand types

- section: Generic helpers
- relevance: 4 - mixed widths truncate silently
- words: 80

What type does the result of `ALIGN(x, a)` have, and how is `a` converted
before the mask is formed? What usage with operands of different widths (a
64-bit value with a 32-bit alignment, a 32-bit value with a 64-bit alignment, a
signed value) is unsafe, and what that looks similar is correct? Start from
`__ALIGN_KERNEL()`.

## align.overflow: Rounding up past the maximum

- section: Generic helpers
- relevance: 4 - a wrapped length passes every later bounds check
- words: 70

What does `ALIGN()` return when rounding up would pass the largest value of
the operand's type, for an unsigned operand and for a signed one under the
compiler options the kernel is built with? What usage on a length or address
that comes from user space, firmware or a device is unsafe, and what that looks
similar is correct? Name in-tree code that guards against it.

## align.round-up-family: Rounding macro families

- section: Generic helpers
- relevance: 3 - three families that look interchangeable and are not
- words: 80

How do `round_up()` and `round_down()`, `roundup()` and `rounddown()`, and
`ALIGN()` and `ALIGN_DOWN()` differ in which multiples they accept, in how many
times they evaluate their arguments and in the type of the result? When is
each the right one? Start from `include/linux/math.h`.

## align.pointer-forms: Aligning pointers

- section: Generic helpers
- relevance: 3 - the integer macros do not compile or do the wrong thing on a pointer
- words: 50

How is a pointer rounded up or down to a boundary, and how is a pointer tested
for alignment, given that `ALIGN()` and `IS_ALIGNED()` do arithmetic on their
first argument? Name the macros, and say what a test on a pointer has to do.

# Page-sized helpers

## align.page-helpers: Page alignment macros

- section: Page helpers
- relevance: 4 - the most used forms, and the argument kinds differ between them
- words: 60

What do `PAGE_ALIGN()`, `PAGE_ALIGN_DOWN()` and `PAGE_ALIGNED()` expand to,
which header defines them, and what kinds of argument does each accept: an
unsigned long, a pointer, a 64-bit physical address on a 32-bit kernel?

## align.page-mask: Masking with the page mask

- section: Page helpers
- relevance: 4 - the open-coded form truncates wide physical addresses
- words: 70

How is `PAGE_MASK` defined, and is the definition the same on every kernel?
What usage of a page mask, or of `~(PAGE_SIZE - 1)`, on a value wider than
unsigned long such as `phys_addr_t` on a 32-bit kernel is unsafe, and what
that looks similar is correct? Start from `include/vdso/page.h`.

## align.pfn-conversions: Addresses and page frame numbers

- section: Page helpers
- relevance: 4 - one of these is named for the wrong unit
- words: 70

What do `PFN_ALIGN()`, `PFN_UP()`, `PFN_DOWN()`, `PFN_PHYS()` and `PHYS_PFN()`
each take and return: a byte address or a page frame number, rounded which
way, of what type? Which of them truncates a physical address on a 32-bit
kernel with wide physical addresses? Start from `include/linux/pfn.h`.

## align.unit-mismatch: Bytes and page frame numbers

- section: Page helpers
- relevance: 3 - both are unsigned long, so the compiler cannot tell
- words: 50

What usage of the page-sized helpers on a page frame number, or of a helper
that works on page frame numbers on a byte address, is unsafe, and what that
looks similar is correct? How does code under `mm/` usually show which unit a
variable holds?

## align.range-to-pages: Pages spanned by a byte range

- section: Page helpers
- relevance: 3 - an off-by-one page that only shows with an unaligned start
- words: 60

How many pages does a byte range touch when it starts at an arbitrary offset
into a page and has an arbitrary length? What usage of `PAGE_ALIGN()` or
`DIV_ROUND_UP()` on the length alone is unsafe for that, and what is correct?
Name in-tree code that does it correctly. Start from `offset_in_page()`.

# Pageblock helpers

## align.pageblock-order: Pageblock size

- section: Pageblocks
- relevance: 4 - it is a constant on some configurations and a variable on others
- words: 80

How is `pageblock_order` defined under each combination of huge page
configuration options, when is it a variable set at boot and by which
function, and what bounds it from above? Start from
`include/linux/pageblock-flags.h`.

## align.pageblock-helpers: Pageblock helper macros

- section: Pageblocks
- relevance: 5 - four macros whose names do not say which way they round
- words: 90

What do `pageblock_nr_pages`, `pageblock_align()`, `pageblock_aligned()`,
`pageblock_start_pfn()` and `pageblock_end_pfn()` expand to, and what unit do
they take? Give a table of what the last four return for a page frame number
that is on a pageblock boundary and for the one just after it, assuming 512
pages per pageblock.

## align.pageblock-end-usage: Range ends and pageblocks

- section: Pageblocks
- relevance: 5 - an off-by-one here is a whole pageblock
- words: 80

Is the value `pageblock_end_pfn()` returns the last page frame of the block or
one past it? What usage of `pageblock_end_pfn()` or `pageblock_align()` on the
end of a range, or of `pageblock_align()` where the start of the containing
block is wanted, is unsafe, and what that looks similar is correct? Name
in-tree code that shows it. Start from `start_isolate_page_range()`.

## align.pageblock-zone-clamp: Pageblocks and zone boundaries

- section: Pageblocks
- relevance: 3 - the helpers know nothing about zones or holes
- words: 60

Can a pageblock extend past the start or the end of a zone, and can it contain
holes? What do callers that walk a zone one pageblock at a time do with the
values `pageblock_start_pfn()` and `pageblock_end_pfn()` return before using
them? Start from `fast_isolate_around()` and `isolate_migratepages_range()` in
`mm/compaction.c`.

## align.pageblock-requirements: Interfaces needing pageblock alignment

- section: Pageblocks
- relevance: 3 - some callers must align and some interfaces align for them
- words: 80

Which interfaces require a range of page frames to be pageblock aligned, and
which align it themselves: page isolation, contiguous range allocation, CMA
areas, memory hotplug, the memory map kept on hotplugged memory? For each say
who does the aligning. Start from `start_isolate_page_range()`,
`alloc_contig_range()` and `CMA_MIN_ALIGNMENT_PAGES`.

## align.pageblock-vs-max-order: Pageblock order and buddy order

- section: Pageblocks
- relevance: 3 - decides whether one free page can cover several pageblocks
- words: 60

What is the relation between `pageblock_order`, `MAX_PAGE_ORDER` and the order
of a PMD-sized huge page, is it enforced at build time, and can one free buddy
page span more than one pageblock?

# Allocators

## align.kmalloc-guarantee: kmalloc alignment guarantee

- section: Allocator alignment
- relevance: 5 - reviewers report a missing alignment that the allocator guarantees
- words: 70

What alignment does `kmalloc()` guarantee for a size that is a power of two,
for other sizes, and as a minimum for every size? Does the guarantee hold with
slab debugging or KASAN enabled, and where is it documented?

## align.minalign-constants: Minimum alignment constants

- section: Allocator alignment
- relevance: 4 - the relation between them changed and DMA safety rests on it
- words: 80

What are `ARCH_KMALLOC_MINALIGN`, `ARCH_SLAB_MINALIGN` and
`ARCH_DMA_MINALIGN`, and how do their defaults derive from each other? On
which configuration can the first be smaller than the third, and what does
that mean for a `kmalloc()` buffer used for DMA?

## align.page-aligned-origin: Page aligned and page allocated

- section: Allocator alignment
- relevance: 4 - alignment says nothing about which allocator owns the memory
- words: 70

What usage that infers from `PAGE_ALIGNED()` on a pointer that the memory came
from the page allocator is unsafe, and what usage that assumes a `kmalloc()`
buffer cannot be page aligned is wrong? What should code test instead when it
needs to know where memory came from?

## align.other-allocators: Alignment from other allocators

- section: Allocator alignment
- relevance: 3 - each allocator promises something different
- words: 90

What alignment do `alloc_pages()` of a given order, `vmalloc()`,
`kmem_cache_alloc()` from a cache created with an explicit alignment,
`dma_alloc_coherent()` and `kvmalloc()` each guarantee? A table. Which
allocation interfaces take an explicit alignment argument?

# Neighbouring subjects

## align.unaligned-access: Unaligned access helpers

- section: Outside the guide's triggers
- relevance: 2 - a different subject that shares the word; measured, not built
- words: 60

Which header provides `get_unaligned()`, `put_unaligned()` and the
endian-specific forms in this tree, how are they implemented, and what does
`CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS` change? Start from
`Documentation/core-api/unaligned-memory-access.rst`.

## align.packed-aligned: Packed and aligned attributes

- section: Outside the guide's triggers
- relevance: 2 - a different subject that shares the word; measured, not built
- words: 60

What do `__packed` and `__aligned()` do to a structure's layout and to the
accesses the compiler generates for its members? What usage of a pointer to a
member of a packed structure is unsafe, and what that looks similar is
correct?

## align.cacheline-attrs: Cache line annotations

- section: Outside the guide's triggers
- relevance: 2 - a different subject that shares the word; measured, not built
- words: 60

What is the difference between `____cacheline_aligned`, `__cacheline_aligned`,
`____cacheline_aligned_in_smp` and `____cacheline_internodealigned_in_smp`,
and what annotation does this tree provide for a structure member that a
device writes by DMA? Start from `include/linux/cache.h`.

# Changing the implementation

## align.copies: Copies of the definitions

- section: What a change must preserve
- relevance: 3 - the userspace test builds carry their own copies
- words: 70

Which other copies of the alignment and pageblock macros exist outside
`include/`: under `tools/`, in the userspace test harnesses for memblock and
for VMAs, under `scripts/`, in Rust? Which of them must a change to the kernel
macros keep in step, and are the primitives the macros expand to part of the
UAPI?
