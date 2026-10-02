# What the io-accessors measurement found

Three models were asked the 27 questions in `io-accessors-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and
C; which models they were does not matter here. Reader A said it assumed
kernels 6.12 to 6.15 and reader C 6.14 to 6.17; both describe the accessor
families, their byte order and their barriers correctly, and reader C needed
the fewest corrections. Reader B said 6.10 to 6.12 and was wrong about
fundamentals: what the barrier hooks default to, what the relaxed forms keep,
what a big-endian accessor does, and what is unsafe about a FIFO remainder.
The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

The accessors are old and their outline is well known. What the readers got
wrong is where the generic code now lives, which configuration compiles which
branch of the generic header, what the documents say against what the headers
define, and the ordering rules at the edges: what a raw access may be merged
with, which barrier repairs a relaxed access next to DMA memory, and who pays
for ordering writes against a spinlock.

## What all three readers got wrong

- **What the documents describe that the headers do not define.** None could
  name anything. `Documentation/driver-api/device-io.rst` tells the reader to
  use __readb() "and friends" for relaxed ordering and names ins() and outs();
  no generic header defines any of them. It lists `ioread64_rep()` and
  `iowrite64_rep()`, which exist only as inlines in `include/asm-generic/io.h`
  under `CONFIG_64BIT` and without `CONFIG_GENERIC_IOMAP`; `lib/iomap.c` has
  only the 8, 16 and 32-bit forms. Its `ioremap_uc()` text still mentions
  ia64. Reader B made `Documentation/driver-api/io_ordering.rst` the authority
  on ordering; that file is one example of a read-back before an unlock, and
  the authority is the kernel I/O barrier effects section of
  `Documentation/memory-barriers.txt`.
- **Big-endian accessors.** `ioread64be()` and `iowrite64be()` are defined in
  `include/asm-generic/io.h` only under `CONFIG_64BIT` and without
  `CONFIG_GENERIC_IOMAP`; with it, `lib/iomap.c` has only
  `__ioread64be_lo_hi()` and `__ioread64be_hi_lo()` and one of the
  `include/linux/io-64-nonatomic-lo-hi.h` or `-hi-lo.h` headers supplies the
  name. Reader A built `ioread32be()` on the raw accessor and reader B said it
  does not swap; it is `swab32(readl(addr))`, so it has the barriers of
  `readl()`. Reader B offered readl_be and friends, which only some
  architectures have.
- **How an architecture overrides an accessor.** Readers A and C said the
  architecture header includes `<asm-generic/io.h>` last; only the overrides
  have to come before it (arm64 defines `ioremap_cache()` after it). A macro
  of the same name with arguments counts as an override, not only
  `#define readl readl`. The port accessors are guarded by
  `#if !defined(inb) && !defined(_inb)`, so `_inb()` can be overridden on its
  own. Reader A said the repeating forms wrap `readl()`; `ioread32_rep()`
  calls `readsl()`, and only without `CONFIG_GENERIC_IOMAP`. Reader B listed
  __iormb() and __iowmb() as generic hooks; they are private to arm, arc and
  arm64.
- **Who bypasses the generic code.** Readers A and B said some architectures
  do not include `include/asm-generic/io.h`; every `arch/*/include/asm/io.h`
  does. What is bypassed is single functions: x86, arm, powerpc, sparc, sh,
  alpha, m68k and s390 define their own `memcpy_toio()`, `memcpy_fromio()` and
  `memset_io()`, and so does um under `CONFIG_INDIRECT_IOMEM`
  (`include/asm-generic/logic_io.h`). Reader C implied only x86 builds `lib/iomap.c`;
  `CONFIG_GENERIC_IOMAP` is also selected by m68k and by powerpc's
  `PPC_INDIRECT_PIO`. Readers B and C left out `CONFIG_MMU` among the options
  that pick a branch of the header, and reader B `CONFIG_64BIT` and
  `CONFIG_GENERIC_IOREMAP` as well.
- **64-bit `ioread64()`.** Each was partly wrong about what it resolves to.
  Without `CONFIG_GENERIC_IOMAP` on 64-bit it is `readq()`. With it, nothing
  defines `ioread64()` until a nonatomic header is included, and then it is
  `__ioread64_lo_hi()` or `__ioread64_hi_lo()` from `lib/iomap.c` according to
  which header: still one `readq()` for MMIO, two `inl()` for a port.
- **Writes and spinlocks.** All knew a driver calls nothing. The detail was
  wrong each time: only powerpc (64-bit) and riscv select `ARCH_HAS_MMIOWB`;
  mips and sh call `mmiowb()` on every unlock; loongarch defines `__io_aw()`
  as `mmiowb()`, so it pays after every `writel()`; generic
  `writel_relaxed()` does not call `__io_aw()` at all. Reader B cited ia64,
  which is gone, and said io_ordering.rst retires mmiowb(), which it never
  mentions.
- **`struct iosys_map` on 32-bit.** A `u64` access to I/O memory goes through
  `memcpy_fromio()` and `memcpy_toio()`; `readq()` is used only under
  `CONFIG_64BIT`. Reader B said the I/O side uses `ioread32()` and friends; it
  uses `readl()` and friends.
- **MMIO tracing** is offered by arm64 and s390 (readers A and C said arm64
  only, reader B said x86), is implemented in `lib/trace_readwrite.c`, and is
  switched off for one file with `__DISABLE_TRACE_MMIO__`.

## What only some readers got wrong

- **Reader B on fundamentals.** The barrier hooks all default to nothing (they
  default to `barrier()`, `rmb()`, `wmb()` and `mmiowb_set_pending()`); the
  relaxed forms have no ordering against other I/O (they keep order to the
  same peripheral); the plain forms are a full barrier; the raw forms are
  "bus-endian" (native); `dma_rmb()` repairs a relaxed status read before
  reading DMA memory (the `dma_*()` barriers do not order MMIO, `rmb()` does);
  `ioremap_uc()` and `ioremap_np()` fall back to `ioremap()` (both return
  NULL) and `ioremap_cache()` has a generic fallback (it has none);
  `io_stop_wc()` flushes the write-combining buffer (it only stops merging
  across it, is empty by default and is `dgh()` on arm64); `__iomem` is
  address space 2 (it is a named address space); a bad cookie in `IO_COND`
  hits BUG() (a `WARN()`, ten times at most); `inb()` goes through
  `ioport_map()` and `readb()` (it is `__raw_readb()` at `PCI_IOBASE` plus the
  port, between `__io_pbr()` and `__io_par()`); the generic `inb_p()` adds a
  delay (it calls `inb()`); `inb()` without `CONFIG_HAS_IOPORT` is undefined
  (it is declared with `__compiletime_error()`).
- **Reader B on the FIFO remainder.** It knew the string forms do not swap,
  but gave an overlapping byte access as the unsafe case and missed the one
  the guide is about: a tail moved with `writel()` or `readl()` is swapped on
  big-endian kernels while the bulk moved with `writesl()` was not.
- **Where the code is** (readers A and B). Both named lib/pci_iomap.c;
  `pci_iomap()` is in `drivers/pci/iomap.c`. Reader B put the bodies of
  `memcpy_toio()`, `memcpy_fromio()` and `memset_io()` inline in the generic
  header doing byte copies, and said `__iowrite32_copy()` uses `writel()`;
  the bodies are in `lib/iomem_copy.c` and use `__raw_readq()` or
  `__raw_readl()` on a `long`-aligned I/O side with `get_unaligned()` on the
  RAM side, and `lib/iomap_copy.c` uses `__raw_writel()`. `lib/iomap.c` is
  built only with `CONFIG_GENERIC_IOMAP`.
- **`__io_aw()`** (readers A and B) defaults to `mmiowb_set_pending()`, not to
  nothing; it is empty only without `CONFIG_MMIOWB`.
- **Raw accessors** (readers A and B). Both said an access is never split or
  merged. device-io.rst says a single access is usually not split but
  consecutive ones can be combined on the bus, and that in portable code they
  are safe for memory behind a device bus, not for MMIO registers.
- **Write-combining** (readers A and B). `io_stop_wc()` is empty by default,
  not a compiler barrier (reader A) and not a flush (reader B). device-io.rst
  lists speculative reads, reordering, repeated writes and combining; neither
  prefetching nor buffering is its wording, and nothing orders such accesses
  against `ioremap()` register accesses without a barrier.
- **Port I/O under `CONFIG_INDIRECT_PIO`** (readers A and C).
  `include/linux/logic_pio.h` defines `inb` as `logic_inb`, so `_inb()` is not
  always what runs.
- **DMA ordering examples** (reader C). The rule was right and the in-tree
  examples were not: `igb_tx_map()` has a `dma_wmb()`, not a `wmb()`, before
  its doorbell `writel()`, and `mlx5e_notify_hw()` puts `wmb()` before a `__raw_writeq()`.
- **Managed mapping helpers.** `__devm_ioremap_resource()` reports with
  `dev_err_probe()`, fails with `-ENOMEM` and no `ioremap()` fallback when
  `ioremap_np()` returns NULL, and releases the region it requested (reader
  A); it has no size check (reader B); `of_mmio_is_nonposted()` looks at the
  node and then its parent (readers A and C). `IOMEM_ERR_PTR()` is in
  `include/linux/err.h` (reader C).
- **Polling helpers.** There is no extra read after the time runs out; expiry
  is sampled before each read, so the last read tested comes after the
  deadline (reader A). The value is an lvalue the macro assigns, not a pointer
  (reader B). The sleeping form sleeps only when the sleep argument is
  non-zero (reader C).
- **PCI BAR cookies** (reader B). An I/O BAR gives an `ioport_map()` cookie
  that only the `ioread32()` family may take; `inb()` does not.

## What the readers already knew

Readers A and C: the byte order and barriers of every family in the generic
header, that a string accessor is a raw access to a fixed address with no swap
and no barrier and a naturally aligned buffer, the FIFO remainder rule and the
i3c helpers that show it, the repeating `ioread32()` forms, the `IO_COND`
cookie ranges, the five ordering guarantees and what the relaxed forms keep,
which barrier repairs a relaxed access, how a posted write is flushed, what
`__iomem` is under sparse, the fallbacks of the `ioremap()` variants, and
(reader C) where every file is.

## Where the hand-written guide is stale

- It names DMA buffers among the uses of the string accessors. They access one
  address over and over, and the memory model document says they are for
  FIFOs on peripherals that cannot do DMA, with only the ordering of the
  relaxed forms.
- It says there are two families. There are at least nine, and its trigger
  loads it for `__raw_writel()` and `__raw_readl()`, of which it says only
  that the string forms are built on them: nothing on what they do not order
  or where the documentation allows them.
- "FIFOs should use stream accessors exclusively" is an absolute. What is
  unsafe is mixing families on one byte stream; a FIFO of register-format
  words is correctly written with `writel()`.
- It says nothing of ordering, of `memcpy_toio()` and the other block copies
  that also skip the swap, or of `ioread32_rep()`, which is the same loop
  under another name.
- Its description of the generic `readl()` and `readsl()` and its pointer to
  `i3c_writel_fifo()` and `i3c_readl_fifo()` in `drivers/i3c/internals.h` are
  correct in this tree.
- Its last quick check tells a reviewer what to flag. The build set asks for
  the unsafe usage and the correct usage that looks like it.

## What was left out of the build set and why

The build set has 10 of the 27 questions. The hand-written guide is 458 words,
and a guide that short is sized to 600 words, give or take twenty percent, with
no question budgeted under 40; the ten ask for 520 words. It is weighted
towards what loads the guide: string, raw and block-copy accesses to a FIFO or
buffer. It was first cut to eight questions and 390 words, which left answers
of 35 to 55 words that were fragments. Two questions came back with the room:
the barrier hooks, whose defaults both builders had been squeezing in under the
family table and where readers A and B had `__io_aw()` wrong, and the
checklist for a change to the generic code, which is the question all three
readers did worst on. Left out:

- What readers A and C answer and only the oldest reader does not: string
  accessor semantics and the repeating forms (the family table has their
  rows), cookie dispatch, port I/O, posted writes, the `__iomem` annotation,
  the mapping variants, PCI BAR mapping.
- What all got partly wrong but few patches under this guide's trigger turn
  on: the documents, the big-endian and 64-bit forms, writes inside spinlocks
  (the readers had the verdict right and the architecture list wrong),
  write-combining mappings, the managed mapping helpers, the polling helpers,
  `struct iosys_map`, MMIO tracing. They stay in the measurement set; a guide
  for `ioremap()` and device mappings would want several of them.

Both questions on changing the implementation are kept: the override
convention says what is derived from what, and the checklist says which
configurations and which architectures compile something other than the
generic code. Four questions were reworded, here and in the measurement set,
so that none presupposes its answer: the override question no longer offers
the string and block-copy forms as its example of what is derived, the hooks
question asks whether the port accessors have a set of their own, the
checklist asks which architectures use their own code in place of the header
or of single functions from it, and the family table and the checklist ask for
macro and option names in full.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           41        25%     10      8   6.12 to 6.15
reader B           68        76%      0     27   6.10 to 6.12
reader C           27        21%     14      6   6.14 to 6.17

question                        reader A      reader B      reader C   verdict
ioacc.core-files                 8% ( 3)      59% ( 7)       0% ( 0)   weak: reader B
ioacc.docs                      65% ( 2)      90% ( 3)      58% ( 2)   all weak
ioacc.family-table               4% ( 1)      45% ( 6)       0% ( 0)   weak: reader B
ioacc.barrier-hooks              7% ( 1)      75% ( 1)      18% ( 2)   weak: reader B
ioacc.string-accessors           0% ( 0)      41% ( 0)       0% ( 0)   weak: reader B
ioacc.rep-accessors              0% ( 0)      77% ( 1)       0% ( 0)   weak: reader B
ioacc.fifo-remainder             3% ( 1)      81% ( 2)       0% ( 0)   weak: reader B
ioacc.raw-accessors             47% ( 2)      82% ( 1)      13% ( 0)   weak: reader A, reader B
ioacc.memcpy-io                 25% ( 1)      87% ( 3)      10% ( 1)   weak: reader B
ioacc.iomap-dispatch            18% ( 1)      89% ( 2)       0% ( 0)   weak: reader B
ioacc.big-endian-accessors      43% ( 1)      76% ( 3)      40% ( 1)   all weak
ioacc.sixty-four-bit            24% ( 1)      71% ( 1)      26% ( 1)   weak: reader B
ioacc.port-io                   17% ( 1)      77% ( 4)      32% ( 1)   weak: reader B
ioacc.ordering-guarantees       36% ( 2)      92% ( 3)      14% ( 1)   weak: reader B
ioacc.dma-ordering               0% ( 0)      75% ( 1)      48% ( 2)   weak: reader B, reader C
ioacc.spinlock-ordering         47% ( 1)      81% ( 1)      38% ( 2)   weak: reader A, reader B
ioacc.posted-writes             25% ( 1)      89% ( 1)       0% ( 0)   weak: reader B
ioacc.wc-mappings               61% ( 1)      82% ( 1)       6% ( 0)   weak: reader A, reader B
ioacc.iomem-annotation           3% ( 1)      72% ( 2)       6% ( 1)   weak: reader B
ioacc.ioremap-variants          16% ( 2)      53% ( 4)      10% ( 1)   weak: reader B
ioacc.mapping-helpers           34% ( 3)      85% ( 3)      14% ( 1)   weak: reader B
ioacc.pci-iomap                  9% ( 2)      84% ( 2)      25% ( 1)   weak: reader B
ioacc.iosys-map                 42% ( 1)      77% ( 2)      39% ( 1)   weak: reader A, reader B
ioacc.poll-helpers              13% ( 1)      71% ( 3)      31% ( 1)   weak: reader B
ioacc.mmio-tracing              17% ( 2)      78% ( 4)      43% ( 1)   weak: reader B, reader C
ioacc.arch-override             55% ( 6)      79% ( 2)      56% ( 3)   all weak
ioacc.change-checklist          78% ( 3)      90% ( 5)      61% ( 4)   all weak
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `ioacc.spinlock-ordering`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `ioacc.iomap-dispatch`, `ioacc.sixty-four-bit`, `ioacc.posted-writes`, `ioacc.iomem-annotation`, `ioacc.ioremap-variants`, `ioacc.mapping-helpers`.

## Questions reorganised

Grouped by subject: accessor families (with the two questions on overriding and changing the generic
code), byte order and block access, ordering, pointers and mappings. 19 questions before and after;
none merged or dropped, since each already asked for one thing.
`ioacc.barrier-hooks` no longer repeats what `ioacc.family-table` asks (which hooks sit around an
access) and asks only what each defaults to. `ioacc.change-checklist` asks what compiles a different
branch and where single functions are replaced, not for a list of architectures. `ioacc.memcpy-io`,
`ioacc.sixty-four-bit` and `ioacc.iomem-annotation` lost the clauses that one search answers.
