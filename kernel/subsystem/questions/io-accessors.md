# Questions: I/O Accessors

- guide: io-accessors.md
- title: I/O Accessors

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/io-accessors-measurement.md` is
the wider set the readers were measured on and `catalogue/io-accessors-measurement-results.md`
says what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## ioacc.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## ioacc.core-files: Core files

- section: Finding your way
- relevance: 4 - the generic definitions are spread over headers and lib/

A table and nothing else, job to file: the generic MMIO and port accessors; the `ioread32()`
family that accepts either kind of address; the block-copy helpers for I/O memory; the helpers
for 64-bit registers on hardware that cannot do one 64-bit access; the managed `ioremap()`
wrappers; the generic `ioremap()` implementation; the PCI BAR mapping helpers. Where a reader
is likely to look for a file that does not exist in this tree, or that is only built under one
option, say so in the row. Start from `include/asm-generic/io.h` and `lib/iomap.c`.

# Accessor families

## ioacc.family-table: Per-family byte order and hooks

- section: Accessor families
- relevance: 5 - byte order and barriers differ per family and nothing in a call site shows it

One table of the accessor families a driver chooses among (the plain register accessors, their
relaxed forms, the raw forms, `ioread32()` and its big-endian form, the string forms such as
`readsl()`, `ioread32_rep()`, port `inl()` and its string form `insl()`): for each, what
byte-order conversion the generic implementation does and which barrier hooks, each named in
full, it puts around the access. Start from `include/asm-generic/io.h`.

## ioacc.barrier-hooks: Barrier hooks

- section: Accessor families
- relevance: 4 - an architecture tunes ordering only through these

What does each barrier hook of the register accessors, and of the port accessors if they have
a set of their own, default to when an architecture does not define it, what is each one for,
and under what configuration is a default empty? Start from `__io_br()` and `readl()` in
`include/asm-generic/io.h`.

## ioacc.iomap-dispatch: ioread and iowrite dispatch

- section: Accessor families
- relevance: 4 - decides whether a cookie from a port mapping can be used

With `CONFIG_GENERIC_IOMAP`, how do `ioread32()` and `iowrite32()` tell a port cookie from an
MMIO address, what happens for a value that is neither, and what does a read return then?
Without that option, what are these functions? Start from `IO_COND` in `lib/iomap.c`.

## ioacc.sixty-four-bit: 64-bit accessors

- section: Accessor families
- relevance: 4 - build failures on 32-bit and torn accesses both start here

Under which configuration does the generic header define `readq()` and `writeq()`, what must a
driver include to use those names when it does not and what does it get, and what do
`ioread64()` and `iowrite64()` resolve to in each case? Start from
`include/linux/io-64-nonatomic-lo-hi.h` and `include/linux/io-64-nonatomic-hi-lo.h`.

## ioacc.arch-override: Overriding an accessor

- section: Accessor families
- relevance: 4 - the wrong define order silently picks the generic version

By what convention does an architecture replace one accessor or one barrier hook from the
generic header, what must its own I/O header do and in which order (give one architecture's
header by its full path as the example), and which other accessors does the generic header
then build on top of a primitive the architecture has replaced? Write every accessor and hook
name in full, in its 32-bit form, never as a pattern.

## ioacc.change-checklist: Changing the generic accessors

- section: Accessor families
- relevance: 4 - the header is included by almost every driver on most architectures

By what mechanisms can an architecture or a configuration option replace a function defined in
`include/asm-generic/io.h`, `lib/iomap.c` or `lib/iomem_copy.c`, so that a change to the generic
function does not reach every build? Which documents specify the behaviour of these accessors?

# Byte order and block access

## ioacc.raw-accessors: Raw accessor guarantees

- section: Byte order and block access
- relevance: 4 - used where a register accessor was needed and the reverse

What do `__raw_readl()` and `__raw_writel()` guarantee about byte order and about ordering against
other accesses, and may an access be split or merged? For what kind of device memory does
`Documentation/driver-api/device-io.rst` say they are safe in portable code, and for what not?

## ioacc.memcpy-io: Block copy helpers

- section: Byte order and block access
- relevance: 4 - the implementation moved and its access widths matter to devices

Which access widths and primitives does the generic implementation of `memcpy_toio()`,
`memcpy_fromio()` and `memset_io()` use on the I/O side and on the memory side, does it
convert byte order or give any ordering or barrier guarantee, and how do `__iowrite32_copy()`
and `__iowrite64_copy()` differ from it?

## ioacc.fifo-remainder: FIFO remainder handling

- section: Byte order and block access
- relevance: 5 - corrupts data on big-endian only, so testing does not find it

What are the requirements for moving the last bytes of a buffer to or from a device FIFO, when the
length is not a multiple of the access width and `writesl()` or `readsl()` moved the whole words,
in order to assure safe usage? Name in-tree code that shows it. Start from `i3c_writel_fifo()`.

# Ordering

## ioacc.ordering-guarantees: Portable ordering guarantees

- section: Ordering
- relevance: 5 - every choice between a plain and a relaxed accessor rests on this list

What does the memory model documentation guarantee for the plain register accessors on a
mapping with default attributes, and which of those guarantees do the relaxed forms, the
string forms and the port accessors keep? Start from the section on kernel I/O barrier effects
in `Documentation/memory-barriers.txt`.

## ioacc.spinlock-ordering: Writes inside spinlocks

- section: Ordering
- relevance: 4 - the documents in the tree do not say the same thing

Is a `writel()` issued inside a spinlocked section ordered before a `writel()` to the same device
from another CPU that takes the lock afterwards, and by what mechanism? Must a driver call
anything itself to get that ordering? Start from `mmiowb_set_pending()` and
`Documentation/driver-api/io_ordering.rst`.

## ioacc.posted-writes: Posted writes

- section: Ordering
- relevance: 4 - a delay after a write measures nothing unless the write has landed

What must a driver do to be sure that a `writel()` has reached the device before it goes on, for
example before a `udelay()` or before freeing what the device was using? What does
`Documentation/driver-api/device-io.rst` say about the read used for that when the device may be
resetting?

## ioacc.dma-ordering: Ordering against DMA memory

- section: Ordering
- relevance: 5 - a missing barrier here is silent on x86 and corrupts on arm64

What are the requirements for using `readl_relaxed()` or `writel_relaxed()` next to CPU accesses
to coherent DMA memory, in order to assure safe usage? Which explicit barrier orders such an
access against the accesses to memory, and which barriers do not order MMIO?

# Pointers and mappings

## ioacc.ioremap-variants: ioremap variants

- section: Pointers and mappings
- relevance: 4 - several variants silently fall back or return NULL

One table of the mapping calls a driver chooses among (`ioremap()`, `ioremap_wc()`,
`ioremap_wt()`, `ioremap_uc()`, `ioremap_np()` and `ioremap_cache()`): what each is for, and
what the generic header makes of each when the architecture does not provide it. Start from the
ioremap comment block in `include/asm-generic/io.h` and
`Documentation/driver-api/device-io.rst`.

## ioacc.mapping-helpers: Managed mapping helpers

- section: Pointers and mappings
- relevance: 4 - the failure value differs between helpers that look alike

What do `devm_ioremap()` and `devm_ioremap_resource()` each do beyond calling `ioremap()`, and
what does each return on failure? Under what condition does either create a non-posted mapping?
Start from `lib/devres.c`.

## ioacc.iomem-annotation: The iomem annotation

- section: Pointers and mappings
- relevance: 4 - the only tool that catches a plain dereference of I/O memory

Which uses of an `__iomem` pointer does sparse warn about and which does a normal build catch,
how does code legitimately convert between an `__iomem` pointer and a plain one, and how are
error pointers carried in an `__iomem` pointer?

# Model gaps

## ioacc.model-gaps: Other mistakes models make

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
