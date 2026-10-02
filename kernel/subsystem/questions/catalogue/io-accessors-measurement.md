# Questions: I/O Accessors (measurement set)

- guide: io-accessors.md
- title: I/O Accessors

A wide set of questions about the MMIO and port I/O accessors (the register,
relaxed, raw, string and block-copy families, `ioread32()` and `iowrite32()`
and their kin, ordering against DMA and locks, the `__iomem` annotation and
the `ioremap()` variants), used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written
guide it will replace is 458 words. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## ioacc.core-files: Core files

- section: Finding your way
- relevance: 4 - the generic definitions are spread over headers and lib/
- words: 100

Which files hold the generic definitions of the MMIO and port accessors, the
`ioread32()` family that accepts either kind of address, the block-copy
helpers for I/O memory, the helpers for 64-bit registers on hardware that
cannot do one 64-bit access, the managed `ioremap()` wrappers, the generic
`ioremap()` implementation and the PCI BAR mapping helpers? A table. Start
from `include/asm-generic/io.h` and `lib/iomap.c`.

## ioacc.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the ordering rules are stated in one place only
- words: 70

Which files under `Documentation/` are the authority on the ordering
guarantees of each accessor family, on the differences between the families,
and on the device memory mapping modes? Name anything one of them describes
that the headers in this tree do not define.

# The accessor families

## ioacc.family-table: Accessor families

- section: Families and their semantics
- relevance: 5 - byte order and barriers differ per family and nothing in a call site shows it
- words: 140

Give a table of the accessor families (the plain register accessors, their
relaxed forms, the raw forms, `ioread32()` and its big-endian form, the string
forms such as `readsl()`, `ioread32_rep()`, port `inl()` and its string form
`insl()`), saying for each what byte-order conversion the generic
implementation does and which barrier macros, each named in full, it puts
around the access. Start from `include/asm-generic/io.h`.

## ioacc.barrier-hooks: Barrier hooks

- section: Families and their semantics
- relevance: 4 - an architecture tunes ordering only through these
- words: 80

Which macros does the generic implementation of the register accessors call
before and after the raw access, what does each default to, and what is each
one for? Do the port accessors use the same macros or a set of their own, and
what does that set default to? Start from `__io_br()` and `readl()` in
`include/asm-generic/io.h`.

## ioacc.string-accessors: String accessor semantics

- section: Families and their semantics
- relevance: 5 - the family this guide is loaded for
- words: 80

In the generic implementation, what does one iteration of `readsl()` or
`writesl()` do: which primitive performs the access, is the address advanced,
is the value byte-swapped, and are there barriers before, between or after the
accesses? What alignment does the memory buffer need?

## ioacc.rep-accessors: Repeating ioread and iowrite

- section: Families and their semantics
- relevance: 3 - same job as the string forms through a different path
- words: 60

How are `ioread32_rep()` and `iowrite32_rep()` implemented with and without
`CONFIG_GENERIC_IOMAP`, do they swap bytes or add barriers, and which widths
exist in each configuration?

## ioacc.fifo-remainder: FIFO remainder handling

- section: Families and their semantics
- relevance: 5 - corrupts data on big-endian only, so testing does not find it
- words: 90

When a buffer whose length is not a multiple of the access width is moved to
or from a device FIFO with a string accessor, what usage for the remaining
bytes is unsafe, and what that looks similar is correct? Name in-tree code
that shows the correct form. Start from `i3c_writel_fifo()`.

## ioacc.raw-accessors: Raw accessor guarantees

- section: Families and their semantics
- relevance: 4 - used where a register accessor was needed and the reverse
- words: 80

What do `__raw_readl()` and `__raw_writel()` guarantee about byte order,
ordering against other MMIO accesses, ordering against memory and locks, and
access size? For what kind of device memory does the documentation say they
are safe in portable code, and for what not?

## ioacc.memcpy-io: Block copy helpers

- section: Families and their semantics
- relevance: 4 - the implementation moved and its access widths matter to devices
- words: 90

Where is the generic implementation of `memcpy_toio()`, `memcpy_fromio()` and
`memset_io()`, which access widths and primitives does it use, how does it
treat alignment of each side, and does it give any ordering or barrier
guarantee? How do `__iowrite32_copy()` and `__iowrite64_copy()` differ from
it?

## ioacc.iomap-dispatch: ioread and iowrite dispatch

- section: Families and their semantics
- relevance: 4 - decides whether a cookie from a port mapping can be used
- words: 90

With `CONFIG_GENERIC_IOMAP`, how do `ioread32()` and `iowrite32()` tell a port
cookie from an MMIO address, what happens for a value that is neither, and
what does a read return then? Without that option, what are these functions?
Start from `IO_COND` in `lib/iomap.c`.

## ioacc.big-endian-accessors: Big-endian registers

- section: Families and their semantics
- relevance: 3 - a driver for a big-endian block must not open-code the swap twice
- words: 60

Which generic accessors exist for a device whose registers are big-endian, how
does the generic implementation build them from the little-endian ones, and
which widths are available?

## ioacc.sixty-four-bit: 64-bit accessors

- section: Families and their semantics
- relevance: 4 - build failures on 32-bit and torn accesses both start here
- words: 90

Under which configuration does the generic header define `readq()` and
`writeq()`, what do `include/linux/io-64-nonatomic-lo-hi.h` and
`include/linux/io-64-nonatomic-hi-lo.h` provide when it does not, and what do
`ioread64()` and `iowrite64()` resolve to in each case?

## ioacc.port-io: Port I/O

- section: Families and their semantics
- relevance: 3 - port I/O no longer compiles everywhere
- words: 80

How does the generic header implement `inb()` and `outb()`, what do
`CONFIG_HAS_IOPORT` and `CONFIG_HAS_IOPORT_MAP` each control, what happens to
code that calls `inb()` when `CONFIG_HAS_IOPORT` is not set, and what do the
variants such as `inb_p()` do in the generic header?

# Ordering

## ioacc.ordering-guarantees: Portable ordering guarantees

- section: Ordering
- relevance: 5 - every choice between a plain and a relaxed accessor rests on this list
- words: 110

List the ordering guarantees the memory model documentation gives for the
plain register accessors on a mapping with default attributes, and say which
of them the relaxed forms, the string forms and the port accessors keep. Start
from the section on kernel I/O barrier effects in
`Documentation/memory-barriers.txt`.

## ioacc.dma-ordering: Ordering against DMA memory

- section: Ordering
- relevance: 5 - a missing barrier here is silent on x86 and corrupts on arm64
- words: 90

What usage of a relaxed, raw or string accessor next to CPU accesses to
coherent DMA memory (descriptors written before a doorbell, data read after a
status register) is unsafe, and what that looks similar is correct? Which
explicit barrier makes the relaxed form correct?

## ioacc.spinlock-ordering: Writes inside spinlocks

- section: Ordering
- relevance: 4 - the documents in the tree do not say the same thing
- words: 90

Is a `writel()` issued inside a spinlocked section ordered before a `writel()`
to the same device from another CPU that takes the lock afterwards? By what
mechanism, on which architectures does it cost anything, and must a driver
call anything itself? Start from `mmiowb_set_pending()` and
`Documentation/driver-api/io_ordering.rst`.

## ioacc.posted-writes: Posted writes

- section: Ordering
- relevance: 4 - a delay after a write measures nothing unless the write has landed
- words: 80

What does a driver have to do to be sure a `writel()` has reached the device
before it goes on, for example before a `udelay()` or before freeing what the
device was using, and what does the documentation say about the read used for
that when the device may be resetting?

## ioacc.wc-mappings: Write-combining mappings

- section: Ordering
- relevance: 3 - the accessor guarantees do not carry over
- words: 70

Which of the accessor ordering guarantees hold for a mapping obtained with
`ioremap_wc()`, what may the CPU do to accesses through such a mapping, and
what is `io_stop_wc()` for?

# Pointers and mappings

## ioacc.iomem-annotation: The iomem annotation

- section: Pointers and mappings
- relevance: 4 - the only tool that catches a plain dereference of I/O memory
- words: 80

What does `__iomem` expand to under sparse and in a normal build, which uses
of such a pointer does sparse warn about, how does code legitimately convert
between an `__iomem` pointer and a plain one, and how are error pointers
carried in an `__iomem` pointer?

## ioacc.ioremap-variants: Mapping variants

- section: Pointers and mappings
- relevance: 4 - several variants silently fall back or return NULL
- words: 110

Give a table of `ioremap()`, `ioremap_wc()`, `ioremap_wt()`, `ioremap_uc()`,
`ioremap_np()` and `ioremap_cache()`: what each is for, and what the generic
header makes of each when the architecture does not provide it. Start from the
ioremap comment block in `include/asm-generic/io.h` and
`Documentation/driver-api/device-io.rst`.

## ioacc.mapping-helpers: Managed mapping helpers

- section: Pointers and mappings
- relevance: 4 - the failure value differs between helpers that look alike
- words: 90

What do `devm_ioremap()` and `devm_ioremap_resource()` each do beyond calling
`ioremap()`, what does each return on failure, and how does a mapping end up
non-posted without the driver asking? Start from `lib/devres.c`.

## ioacc.pci-iomap: PCI BAR mapping

- section: Pointers and mappings
- relevance: 3 - the returned cookie restricts which accessors may be used
- words: 70

What does `pci_iomap()` return for a memory BAR and for an I/O BAR, which
accessor families may be used on the result in each case, and how is it
unmapped?

## ioacc.iosys-map: System or I/O memory

- section: Pointers and mappings
- relevance: 2 - confined to graphics and a few other users
- words: 60

What is `struct iosys_map`, which helpers read, write and copy through it, and
which accessor does it use when the mapping is I/O memory? Start from
`include/linux/iosys-map.h`.

## ioacc.poll-helpers: Register polling helpers

- section: Pointers and mappings
- relevance: 3 - used in most drivers and easy to call from the wrong context
- words: 80

What do `readl_poll_timeout()` and `readl_poll_timeout_atomic()` take and
return, what is the difference in the context each may be called from, what
does the condition get evaluated against after the time has run out, and which
accessor variants have such helpers? Start from `include/linux/iopoll.h`.

## ioacc.mmio-tracing: MMIO access tracing

- section: Pointers and mappings
- relevance: 2 - explains code in every generic accessor
- words: 60

What does `CONFIG_TRACE_MMIO_ACCESS` add to the generic accessors, which
accessor families are traced and which are not, which architectures offer it,
and how does one file opt out?

# Changing the implementation

## ioacc.arch-override: Overriding an accessor

- section: What a change must preserve
- relevance: 4 - the wrong define order silently picks the generic version
- words: 80

By what convention does an architecture replace one accessor or one barrier
hook from the generic header, what must its own I/O header do and in which
order (give one architecture's header by its full path as the example), and
which other accessors does the generic header then build on top of a primitive
the architecture has replaced? Write every accessor and hook name in full, in
its 32-bit form, never as a pattern.

## ioacc.change-checklist: Changing the generic accessors

- section: What a change must preserve
- relevance: 4 - the header is included by almost every driver on most architectures
- words: 80

What must a change to `include/asm-generic/io.h`, `lib/iomap.c` or
`lib/iomem_copy.c` keep working: which configuration options, each `CONFIG_`
name in full, compile different branches of them, which architectures use
their own code in place of the generic header or of single functions from it,
and which documents describe the behaviour and would have to change with it?
