# Questions: Alignment Helpers

- guide: alignment.md
- title: Alignment Helpers

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/alignment-measurement.md` is the
wider set the readers were measured on and `catalogue/alignment-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## align.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## align.core-files: Core files

- section: Finding your way
- relevance: 4 - the definitions are spread over several headers and some have moved

A table and nothing else, job to header, each header as its full path from the top of the tree:
the generic round-up, round-down, test and pointer macros; the primitives they expand to; the
page-sized forms; the page size and page mask; the conversions between byte addresses and page
frame numbers; the pageblock forms; the macros that round to a power of two or to an arbitrary
multiple. Where a reader is likely to look in a header that only includes another, say so in
the row. Start from `include/linux/align.h`.

# Generic helpers

## align.generic-contract: Power-of-two alignment argument

- section: Generic helpers
- relevance: 5 - a wrong argument gives a plausible wrong number and nothing warns

What must the alignment argument of `ALIGN()`, `ALIGN_DOWN()` and `IS_ALIGNED()` be for the result
to be right, and does anything check it at build time or at run time? What is used to round to an
arbitrary multiple?

## align.rounding-results: Rounding results

- section: Generic helpers
- relevance: 5 - a caller that wants the next boundary gets its input back when the input is already aligned

What do `ALIGN()` and `ALIGN_DOWN()` return for an input that is already aligned, and what do they
compute when the alignment argument is one that they do not support?

## align.result-type: Operand types

- section: Generic helpers
- relevance: 4 - mixed widths truncate silently

What type does the result of `ALIGN(x, a)` have, and how is `a` converted before the mask is
formed? What are the requirements for the types of `x` and `a` in order to assure safe usage?
Start from `__ALIGN_KERNEL()`.

## align.overflow: Rounding up past the maximum

- section: Generic helpers
- relevance: 4 - a wrapped length passes every later bounds check

What does `ALIGN()` return when rounding up would pass the largest value of the operand's type,
for an unsigned operand and for a signed one under the compiler options the kernel is built with?
What are the requirements for a length or address that comes from outside the kernel before it is
passed to `ALIGN()`, in order to assure safe usage? Name in-tree code that guards against the
overflow.

## align.copies: Tools, scripts and Rust copies

- section: Generic helpers
- relevance: 3 - the userspace test builds carry their own copies

Where outside `include/` does the tree keep copies of the kernel's alignment and pageblock macros,
and which of the copies does a script compare with the original? Does any copy give a different
result from the C macro at the limit of the type?

## align.uapi-primitives: UAPI alignment primitives

- section: Generic helpers
- relevance: 3 - whether user space can see a macro decides how freely a patch may change it

Are `__ALIGN_KERNEL()` and `__ALIGN_KERNEL_MASK()` part of the UAPI, and what are the requirements
for a change to them in order to assure safe usage?

# Page helpers

## align.page-helpers: Page alignment macros

- section: Page helpers
- relevance: 4 - the most used forms, and the argument kinds differ between them

What types of argument do `PAGE_ALIGN()`, `PAGE_ALIGN_DOWN()` and `PAGE_ALIGNED()` each accept,
and what type does each give back? Say what each expands to only where that explains the
difference.

## align.pfn-conversions: Addresses and page frame numbers

- section: Page helpers
- relevance: 4 - one of these is named for the wrong unit

Which of `PFN_ALIGN()`, `PFN_UP()`, `PFN_DOWN()`, `PFN_PHYS()` and `PHYS_PFN()` take and
return a byte address and which a page frame number, which way does each round, and which of
them truncates a physical address on a 32-bit kernel with wide physical addresses? Start from
`include/linux/pfn.h`.

## align.page-mask: Masking with the page mask

- section: Page helpers
- relevance: 4 - the open-coded form truncates wide physical addresses

How is `PAGE_MASK` typed, and does a configuration option change its definition? What are the
requirements for masking a value wider than unsigned long, such as a `phys_addr_t` on a 32-bit
kernel, with `PAGE_MASK` or with `~(PAGE_SIZE - 1)` in order to assure safe usage? Start from
`include/vdso/page.h`.

# Pageblocks

## align.pageblock-order: Pageblock size

- section: Pageblocks
- relevance: 4 - it is a constant on some configurations and a variable on others

When is `pageblock_order` a compile-time constant and when a variable set at boot, what sets
it then, and what bounds it from above and ties it to the largest buddy order? Start from
`include/linux/pageblock-flags.h`.

## align.pageblock-requirements: Interfaces needing pageblock alignment

- section: Pageblocks
- relevance: 3 - some callers must align and some interfaces align for them

For a range of page frames given to page isolation, to contiguous range allocation, to a CMA
area with a fixed base, and to memory online and offline, does the interface round the range
out to pageblocks itself or must the caller, and what does an interface that does not round do
with a range that is not aligned? Start from `start_isolate_page_range()`,
`alloc_contig_range()` and `CMA_MIN_ALIGNMENT_PAGES`.

## align.pageblock-end-usage: Range ends and pageblocks

- section: Pageblocks
- relevance: 5 - an off-by-one here is a whole pageblock

Is the value `pageblock_end_pfn()` returns the last page frame of the block or one past it, and
what does `pageblock_align()` return for a page frame that is already aligned? What are the
requirements for computing the first and the last pageblock of a range with
`pageblock_start_pfn()`, `pageblock_end_pfn()` and `pageblock_align()` in order to assure safe
usage? Name in-tree code that shows it. Start from `start_isolate_page_range()`.

# Allocator alignment

## align.kmalloc-guarantee: kmalloc alignment guarantee

- section: Allocator alignment
- relevance: 5 - reviewers report a missing alignment that the allocator guarantees

What alignment does `kmalloc()` guarantee for a size that is a power of two, for other sizes,
and as a minimum for every size? Does the guarantee hold with slab debugging or KASAN enabled,
and where is it documented?

## align.minalign-constants: Minimum alignment constants

- section: Allocator alignment
- relevance: 4 - the relation between them changed and DMA safety rests on it

How do the defaults of `ARCH_KMALLOC_MINALIGN`, `ARCH_SLAB_MINALIGN` and `ARCH_DMA_MINALIGN`
derive from each other, if they do? On a configuration where `ARCH_KMALLOC_MINALIGN` is smaller
than `ARCH_DMA_MINALIGN`, what decides the minimum alignment of the kmalloc caches, and what are
the requirements for a `kmalloc()` buffer used for DMA in order to assure safe usage? If no
configuration makes it smaller, say so.

## align.page-aligned-origin: Origin of page-aligned memory

- section: Allocator alignment
- relevance: 4 - alignment says nothing about which allocator owns the memory

Does a true result of `PAGE_ALIGNED()` on a pointer say which allocator the memory came from, and
can a `kmalloc()` buffer be page aligned? What does the tree provide for code that needs to know
which allocator memory came from?

# Model gaps

## align.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
