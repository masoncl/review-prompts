# I/O Accessors

## Main structures

### Objects and how they relate

- `void __iomem *` cookie: what it holds depends on which code produced it;
  the generic code has three encodings:

  | Produced by | Cookie holds | Decoded by |
  |---|---|---|
  | `ioremap()`, or `ioport_map()` in `include/asm-generic/io.h` | a mapped virtual address (`PCI_IOBASE + port` for a port) | nothing without `CONFIG_GENERIC_IOMAP`, where `ioread32()` is an inline `readl()` |
  | `ioport_map()` in `lib/iomap.c` (`CONFIG_GENERIC_IOMAP`) | `port + PIO_OFFSET`, not an address | `IO_COND()` in `lib/iomap.c`, at every `ioread32()` |
  | `ioremap()` in `lib/logic_iomem.c` (`CONFIG_INDIRECT_IOMEM`) | `IOREMAP_BIAS` plus an area index plus an offset, not an address | `get_area()`, at every `__raw_readl()` |

- `inb()`: resolves one of three ways: the arch's own definition (search
  `#define inb` under `arch/`), `logic_inb()` under `CONFIG_INDIRECT_PIO`,
  otherwise `_inb()`, which in `include/asm-generic/io.h` is
  `__raw_readb(PCI_IOBASE + addr)` between `__io_pbr()` and `__io_par()`.
- `struct logic_pio_hwaddr`: one range of the port-number space and what backs
  it; all ranges sit on one list in `lib/logic_pio.c`.
  - `LOGIC_PIO_CPU_MMIO` range: a host bridge I/O window at a CPU physical
    address; `pci_register_io_range()` in `drivers/pci/pci.c` registers it and
    `pci_remap_iospace()` maps it at `PCI_IOBASE` plus the port number.
  - `LOGIC_PIO_INDIRECT` range: ports with no memory mapping at all;
    `logic_inb()` calls the range's `struct logic_pio_host_ops`
    (`drivers/bus/hisi_lpc.c` is the registrant).
  - Indirect ranges take port numbers from `MMIO_UPPER_LIMIT` up;
    `ioport_map()` in `include/asm-generic/io.h` returns `NULL` for a port
    above `MMIO_UPPER_LIMIT`.
- `struct logic_iomem_region` and `struct logic_iomem_area`
  (`lib/logic_iomem.c`): emulated MMIO, selected by `UML_IOMEM_EMULATION` in
  `arch/um/Kconfig`. A region is a `struct resource` plus ops that
  `ioremap()` matches against; an area is one live mapping.
  `__raw_readl()` becomes an out-of-line call into the area's ops, so every
  accessor built on the `__raw_` forms reaches the emulation.
- `struct mmiowb_state`: per-CPU by default; links write accessors to
  spinlocks. Generic `writel()` calls `__io_aw()` after the store, which is
  `mmiowb_set_pending()`; `mmiowb_spin_unlock()`, called from
  `do_raw_spin_unlock()`, then issues `mmiowb()` if `mmiowb_pending` is set.
  Both helpers are empty macros without `CONFIG_MMIOWB`.
- `readl()` and `readl_relaxed()` in `include/asm-generic/io.h`: each is built
  directly on `__raw_readl()`; `readl()` is not built on `readl_relaxed()`.
- Arch override points, three levels: the whole accessor (x86 defines
  `readl()`), the `__raw_` form, or the barrier macros `__io_br()`,
  `__io_ar()`, `__io_bw()`, `__io_aw()` and their port counterparts
  `__io_pbr()`, `__io_par()`, `__io_pbw()`, `__io_paw()` (arm64 defines
  `__io_ar()`).
- `readq()` and `writeq()`: the generic ones are under `CONFIG_64BIT`, but an
  arch may define them regardless; `arch/sh/include/asm/io.h` does.
- `struct io_mapping`: hands out per-page windows only under
  `CONFIG_HAVE_ATOMIC_IOMAP`, which depends on `X86_32`. Otherwise
  `io_mapping_init_wc()` maps the whole range with `ioremap_wc()` and
  `io_mapping_map_local_wc()` returns a pointer into that mapping.
- `struct iosys_map` (`include/linux/iosys-map.h`): a tagged pointer to a
  buffer that is either system memory or an `__iomem` cookie; its helpers
  pick `memcpy()` or `memcpy_toio()`, `READ_ONCE()` or `readl()`.
- `struct resource`: describes and claims the physical range; it is not the
  mapping. Its flags can choose the mapping type:
  `devm_ioremap_resource()` in `lib/devres.c` uses `ioremap_np()` when
  `IORESOURCE_MEM_NONPOSTED` is set.
- devres mappings in `lib/devres.c`: the devres entry holds only the cookie;
  release calls `iounmap()` or `ioport_unmap()` on it.
- `struct pcim_addr_devres` in `drivers/pci/devres.c`: holds the cookie plus
  a type and the BAR number; release calls `pci_iounmap()`,
  `pci_release_region()` or both, by type.

## Where to look

**Core files**

| Job | File in this tree | Easy to miss |
|---|---|---|
| `ioread32()` family without `CONFIG_GENERIC_IOMAP` | inlines in `include/asm-generic/io.h`, under `#ifndef CONFIG_GENERIC_IOMAP` and `#ifndef` of each name; the 64-bit ones also under `CONFIG_64BIT` | `ioread32()` calls `readl()` and still takes a port cookie: `ioport_map()` in the same header returns `PCI_IOBASE + port`, or `NULL` above `MMIO_UPPER_LIMIT`. |
| `memcpy_fromio()`, `memcpy_toio()`, `memset_io()` | `lib/iomem_copy.c`, in `lib-y`, under no option | `include/asm-generic/io.h` only declares them; it has no inline bodies. Each body is under `#ifndef` of its own name. |
| `__iowrite32_copy()`, `__ioread32_copy()`, `__iowrite64_copy()` | `lib/iomap_copy.c`, built under `CONFIG_HAS_IOMEM` | `__ioread32_copy()` has no `#ifndef` guard, so an arch cannot override it; the other two have one. |
| 64-bit access split in two 32-bit accesses, either kind of address | inlines in `include/linux/io-64-nonatomic-lo-hi.h` and `include/linux/io-64-nonatomic-hi-lo.h`, for example `ioread64_lo_hi()`; `lib/iomap.c` holds `__ioread64_lo_hi()` and its siblings, under `CONFIG_GENERIC_IOMAP` and `CONFIG_64BIT`, which split only a port cookie | Under `CONFIG_GENERIC_IOMAP` nothing defines `ioread64()` until a driver includes one of the two nonatomic headers. |
| Managed `ioremap()` wrappers | `lib/devres.c`, built under `CONFIG_HAS_IOMEM` | It holds no `pcim_` helper; the `pcim_iomap()` family is in `drivers/pci/devres.c`. `devm_ioremap_resource()` is declared in `include/linux/device/devres.h`, not `include/linux/io.h`. `devm_memremap()` is in `kernel/iomem.c`. |
| `ioremap()` without `CONFIG_MMU` | inline `ioremap()` and `iounmap()` in `include/asm-generic/io.h`, when the arch defines none | No `.c` file: `ioremap()` returns the physical address cast to a pointer, `iounmap()` is empty. |
| PCI BAR mapping helpers | `drivers/pci/iomap.c`; there is no lib/pci_iomap.c | Built under `CONFIG_GENERIC_PCI_IOMAP`, inside `ifdef CONFIG_PCI` in `drivers/pci/Makefile`. With that option and without `CONFIG_PCI`, `include/asm-generic/pci_iomap.h` gives stubs that return `NULL`. |
| `pci_iounmap()` | `lib/iomap.c` under `CONFIG_GENERIC_IOMAP` and `CONFIG_PCI`; otherwise `drivers/pci/iomap.c` under `ARCH_WANTS_GENERIC_PCI_IOUNMAP`; otherwise the arch | `include/asm-generic/io.h` defines `ARCH_WANTS_GENERIC_PCI_IOUNMAP` when `CONFIG_GENERIC_IOMAP` is off and the arch has not defined `pci_iounmap`. |

## Accessor families

**Per-family byte order and hooks**

- `ioread32be()` in `include/asm-generic/io.h`: `swab32(readl(addr))`;
  `iowrite32be()`: `writel(swab32(value), addr)`. Neither calls
  `be32_to_cpu()` or `cpu_to_be32()`; the hooks are those of `readl()` /
  `writel()`.
- Generic `readsl()`, `writesl()`, `insl()`, `outsl()`: no byte swap, no
  barrier hook, no trace call; `insl()` is `readsl()` on
  `PCI_IOBASE + addr`.
- `ioread32()`, `iowrite32()`, `ioread32be()`, `ioread32_rep()` as wrappers
  of `readl()`, `writel()`, `readsl()`: only inside
  `#ifndef CONFIG_GENERIC_IOMAP`. With the option they are the out-of-line
  functions in `lib/iomap.c`.
- `ioread32_rep()` with `CONFIG_GENERIC_IOMAP`: port cookie goes to `insl()`,
  MMIO goes to `mmio_insl()`, by default a private `__raw_readl()` loop in
  `lib/iomap.c` that does not call `readsl()`;
  `arch/powerpc/include/asm/io.h` defines `mmio_insl()` as `readsl()`.
- Without `CONFIG_HAS_IOPORT`, in `include/asm-generic/io.h`: `_inl()`,
  `_outl()`, `insl()`, `outsl()` are still declared, with
  `__compiletime_error()`; a call fails the build rather than being an
  unknown name.

**Barrier hooks**

| Hook | Default in `include/asm-generic/io.h` |
|---|---|
| `__io_br()` | `barrier()` |
| `__io_ar(v)` | `rmb()` if `rmb` is a macro when the header is read, else `barrier()` |
| `__io_bw()` | `wmb()` if `wmb` is a macro when the header is read, else `barrier()` |
| `__io_aw()` | `mmiowb_set_pending()` |
| `__io_pbr()` | `__io_br()` |
| `__io_par(v)` | `__io_ar(v)` |
| `__io_pbw()` | `__io_bw()` |
| `__io_paw()` | `__io_aw()` |

- `__io_aw()`, and `__io_paw()` through it: the one default that is empty,
  when `CONFIG_MMIOWB` is off; `mmiowb_set_pending()` is then
  `do { } while (0)` in `include/asm-generic/mmiowb.h`.
- `__io_br()` default: never empty, a compiler barrier.
- `CONFIG_MMIOWB`: `def_bool y if ARCH_HAS_MMIOWB` and `depends on SMP` in
  `kernel/Kconfig.locks`; a UP build of an architecture that selects
  `ARCH_HAS_MMIOWB` gets the empty `__io_aw()`.
- Port hooks: `arch/riscv/include/asm/io.h` is the only header that defines
  its own; everywhere else port I/O through `_inl()` gets the MMIO hooks.
- Architecture definitions of the MMIO hooks: search `define __io_` under
  `arch/`; only arm64, riscv and loongarch (`__io_aw()` only) have any.

**ioread and iowrite dispatch**

- `IO_COND` in `lib/iomap.c` tests the cookie as an `unsigned long`, in this
  order:

| Cookie | Treated as |
|---|---|
| `>= PIO_RESERVED` | MMIO: `readl()` / `writel()` |
| `> PIO_OFFSET` | port: masked with `PIO_MASK`, then `inl()` / `outl()` |
| anything else | bad: `bad_io_access()` |

- `bad_io_access()`: `WARN()`, at most 10 times in total (static counter);
  no `BUG()`; no access is made.
- Read of a bad cookie: `ioread32()` returns `0xffffffff` (all ones at every
  width); a write is dropped.
- `PIO_OFFSET`, `PIO_MASK`, `PIO_RESERVED`: 0x10000, 0xffff, 0x40000 only
  when the architecture does not define `HAVE_ARCH_PIO_SIZE`;
  `arch/powerpc/include/asm/io.h` sets `PIO_OFFSET` to 0.
- `CONFIG_GENERIC_IOMAP`: selected only by x86, by m68k
  (`if HAS_IOPORT && MMU && !COLDFIRE`) and by `PPC_INDIRECT_PIO`; arm64,
  riscv and arm do not run `lib/iomap.c`.
- Without `CONFIG_GENERIC_IOMAP`, an architecture can still replace the
  inline `ioread32()`: `arch/alpha/kernel/io.c` and
  `arch/parisc/lib/iomap.c` define their own dispatching `ioread32()`, and
  `arch/sparc/include/asm/io_64.h` makes it a macro for `readl`.

**64-bit accessors**

- `ioread64()` / `iowrite64()` resolve as follows, when the architecture
  defines neither:

| Build | No nonatomic header included | Nonatomic header included |
|---|---|---|
| `CONFIG_64BIT`, no `CONFIG_GENERIC_IOMAP` | inline in `include/asm-generic/io.h`, one `readq()` / `writeq()` | unchanged (`#ifndef ioread64`) |
| `CONFIG_64BIT` and `CONFIG_GENERIC_IOMAP` | not defined | `__ioread64_lo_hi()` or `__ioread64_hi_lo()` in `lib/iomap.c` |
| 32-bit | not defined | inline `ioread64_lo_hi()` or `ioread64_hi_lo()`, two `ioread32()` |

- `__ioread64_lo_hi()` and `__ioread64_hi_lo()`: both do one `readq()` for an
  MMIO cookie; they differ only for a port cookie (two `inl()`).
- `ioread64_lo_hi()` called by name: two `ioread32()` on every build, also
  where `ioread64()` is one `readq()`.
- `ioread64_is_nonatomic`: defined whenever the header supplies `ioread64`,
  including the `CONFIG_GENERIC_IOMAP` 64-bit case where MMIO is one
  `readq()`.
- `readq_relaxed()` / `writeq_relaxed()` in `include/asm-generic/io.h`:
  guarded by `defined(readq) && !defined(readq_relaxed)` and
  `defined(writeq) && !defined(writeq_relaxed)`, not by `CONFIG_64BIT`.
- Both nonatomic headers included in one file: the first sets those of
  `readq`, `writeq`, `ioread64` and `iowrite64` that are not yet defined;
  the second only adds its named functions such as `hi_lo_readq()`.

**Overriding an accessor**

- `arch/arm64/include/asm/io.h`: defines `__io_ar(v)` and `__io_bw()`
  directly; `__iormb(v)` and `__iowmb()` are aliases for them, not the other
  way round.
- Generic `readl_relaxed()` / `writel_relaxed()`: built on `__raw_readl()` /
  `__raw_writel()`, never on `readl()` / `writel()`; replacing `readl()`
  alone leaves the generic relaxed form in place.
- Generic `_inl()` / `_outl()`: built on `__raw_readl()` / `__raw_writel()`
  and the port hooks, not on `readl()`; `insl()` / `outsl()` are built on
  `readsl()` / `writesl()`.
- Inline `ioread32()` in `include/asm-generic/io.h`: never calls `inl()`; a
  replaced `inl()` reaches the generic `ioread32()` only through
  `lib/iomap.c`.
- Port accessor guard: `#if !defined(inl) && !defined(_inl)`; an
  architecture may supply either name. `inl` is mapped to `_inl` only after
  `include/linux/logic_pio.h` has been included.
  `arch/mips/include/asm/io.h` supplies `_inl`.
- Hooks `__io_br()`, `__io_ar()`, `__io_bw()`, `__io_aw()`: in
  `include/asm-generic/io.h`, used only inside the generic `readl()` /
  `writel()` bodies and, through the port defaults, `_inl()` / `_outl()`; an
  accessor the architecture replaced ignores them unless it calls them
  itself.
- Users of a replaced primitive outside the generic header, for example:
  - `__raw_readl()` / `__raw_writel()`: `mmio_insl()` and `mmio_outsl()` in
    `lib/iomap.c`; the copy loops in `lib/iomem_copy.c` on 32-bit builds.
  - `readl()` / `writel()`: `lo_hi_readq()` and `hi_lo_readq()` in the
    nonatomic headers; the MMIO branch in `lib/iomap.c`.
  - `inl()` / `insl()`: the port branch in `lib/iomap.c`.

**Changing the generic accessors**

- `lib/iomem_copy.c`: always built (`lib-y`); each of `memset_io()`,
  `memcpy_fromio()`, `memcpy_toio()` sits under `#ifndef` of its own name in
  the `.c` file. There is no `__weak`. An architecture header that defines
  the macro compiles the generic body out.
- `lib/iomap.c` helper guards cover a group, tested on one name:
  `#ifndef mmio_read16be` guards `mmio_read32be()` and `mmio_read64be()`
  too; `#ifndef mmio_insb` guards `mmio_insw()` and `mmio_insl()`; same for
  `pio_read16be`, `pio_write16be`, `mmio_write16be`, `mmio_outsb`.
  The 32-bit name is never tested.
- `arch/powerpc/kernel/iomap.c`: defines only `ioport_map()` and
  `pci_iounmap()`; powerpc `ioread32()` is the generic inline unless
  `CONFIG_GENERIC_IOMAP`.
- Every `arch/*/include/asm/io.h` in this tree includes
  `<asm-generic/io.h>`; what differs is how many names each defines first.
  Search `define readl` under `arch/` before assuming a generic body runs.
- `CONFIG_INDIRECT_IOMEM` (selected by `arch/um/Kconfig`):
  `include/asm-generic/logic_io.h` replaces `__raw_readl()`,
  `__raw_writel()`, `memset_io()`, `memcpy_fromio()`, `memcpy_toio()` with
  out-of-line functions from `lib/logic_iomem.c`.
- `CONFIG_INDIRECT_PIO` (depends on `ARM64`): `include/linux/logic_pio.h`
  maps `inl` to `logic_inl()` and `insl` to `logic_insl()`, only where the
  architecture has not defined that name. `logic_inl()` in
  `lib/logic_pio.c` calls `_inl()` below `MMIO_UPPER_LIMIT`, so a change to
  `_inl()` still reaches it; the generic `insl()` body is not compiled.
- `tools/include/asm-generic/io.h`: a separate copy with its own hook
  defaults; a change to `include/asm-generic/io.h` does not reach it.
- There is no Documentation/core-api/bus-virt-phys-mapping.rst in this
  tree. The documents are `Documentation/driver-api/device-io.rst`,
  `Documentation/memory-barriers.txt` (section "KERNEL I/O BARRIER
  EFFECTS") and `Documentation/driver-api/io_ordering.rst`.

## Byte order and block access

**Raw accessor guarantees**

- Merging: `Documentation/driver-api/device-io.rst` says "multiple consecutive
  accesses can be combined on the bus"; only the no-split property is
  described, and only as "usually atomic".
- `ioremap()` section of the same document: the "No write-combining" property
  "may or may not be enforced when using __raw I/O accessors".
- Safe in portable code: the document's term is "memory behind a device bus";
  the paragraph names neither frame buffers nor prefetchable memory.
- Not safe in portable code: "MMIO registers"; the only reason the paragraph
  gives is ordering ("other MMIO accesses or even spinlocks"), not byte order.

**Block copy helpers**

- Generic `memcpy_toio()`, `memcpy_fromio()`, `memset_io()`: bodies are in
  `lib/iomem_copy.c`; `include/asm-generic/io.h` only declares them.
- I/O side of the generic three: `__raw_readb()` or `__raw_writeb()` until the
  I/O address is `long`-aligned, then `long`-wide `__raw_` accesses, then
  bytes; `readb()` and `writeb()` are not used, so not even their barriers
  apply.
- arm64: defines none of the three, so it runs `lib/iomem_copy.c`; of the
  block copy helpers it overrides only `__iowrite32_copy()` and
  `__iowrite64_copy()` in `arch/arm64/include/asm/io.h`.
- Overrides of the three: search for `define memcpy_toio`.
- `__iowrite64_copy()` without `CONFIG_64BIT`: exists, and calls
  `__iowrite32_copy(to, from, count * 2)`.
- x86: of `__iowrite32_copy()` and `__iowrite64_copy()` it overrides only
  `__iowrite32_copy()`, and only under `CONFIG_X86_64`; `__iowrite64_copy()`
  on x86 is the generic one.
- Fixed access width: not kept by every override; on s390 with `CONFIG_PCI`
  both helpers call `zpci_memcpy_toio()` with a byte count, which chooses its
  own transfer sizes.
- Memory side of generic `__iowrite32_copy()` and `__iowrite64_copy()`:
  dereferences the source as `u32 *` or `u64 *` with no `get_unaligned()`, so
  the source alignment the kerneldoc asks for is not checked or fixed up; the
  generic `memcpy_toio()` reads its source with `get_unaligned()`, so it
  accepts an unaligned source.

**FIFO remainder handling**

- `i3c_writel_fifo()` and `i3c_readl_fifo()`: defined in
  `drivers/i3c/internals.h`.
- Tail in both helpers: `writesl(addr, &tmp, 1)` and `readsl(addr, &tmp, 1)`,
  not `writel()`, `readl()` or `__raw_writel()`.
- Requirement: the tail word goes through the same byte-order convention as
  the body; generic `writesl()` does not swap and generic `writel()` applies
  `__cpu_to_le32()`, both in `include/asm-generic/io.h`.
- **Unsafe usage**: whole words by `writesl()`, `readsl()`, `iowrite32_rep()`
  or `ioread32_rep()`, then the tail by `memcpy()` to or from a `u32` moved
  with `writel()`, `readl()`, `iowrite32()`, `ioread32()` or a `_relaxed`
  form, with no conversion.
  - Unsafe: on a big-endian kernel the tail bytes are reversed relative to
    the body.
  - Safe: tail by the string accessor with count 1, the same accessor as the
    body, as `i3c_writel_fifo()` and `i3c_readl_fifo()` do.
  - Safe: tail by `readl_relaxed()` followed by `cpu_to_le32()` before the
    `memcpy()`, which cancels the swap, as `tegra_i2c_empty_rx_fifo()` in
    `drivers/i2c/busses/i2c-tegra.c` does; the write side needs
    `le32_to_cpu()` after the `memcpy()`.
  - Safe: body and tail both by the same accessor, as `xi3c_writel_fifo()`
    and `xi3c_readl_fifo()` in `drivers/i3c/master/amd-i3c-master.c` do with
    `iowrite32be()` and `ioread32be()`.
- `drivers/i3c/master/svc-i3c-master.c`: does not call the helpers; search for
  `i3c_writel_fifo` to list the drivers that do.

## Ordering

**Portable ordering guarantees**

- `readsX()`, `writesX()`: keep the guarantees of `readX_relaxed()` and
  `writeX_relaxed()`, so on a mapping with default I/O attributes accesses
  from one CPU thread to one peripheral stay in program order; they are not
  unordered. See "KERNEL I/O BARRIER EFFECTS" in
  `Documentation/memory-barriers.txt`.
- `insX()`, `outsX()`: same guarantees as `readsX()` and `writesX()`, so
  weaker than `inX()` and `outX()`, which match `readX()` and `writeX()`.

**Writes inside spinlocks**

- `ARCH_HAS_MMIOWB`: selected only by `arch/powerpc/Kconfig` (if `PPC64`) and
  `arch/riscv/Kconfig`.
- `CONFIG_MMIOWB`: the symbol `include/asm-generic/mmiowb.h` tests; in
  `kernel/Kconfig.locks` it is `ARCH_HAS_MMIOWB` and depends on `SMP`.
  Without it `mmiowb_set_pending()`, `mmiowb_spin_lock()` and
  `mmiowb_spin_unlock()` are empty macros.
- mips and sh: do not select `ARCH_HAS_MMIOWB`; they call `mmiowb()` on every
  unlock, in `queued_spin_release()` in `arch/mips/include/asm/spinlock.h`
  and `arch_spin_unlock()` in `arch/sh/include/asm/spinlock-llsc.h` (used
  under `CONFIG_CPU_SH4A`; `arch/sh/include/asm/spinlock-cas.h` has no such
  call).
- loongarch: `__io_aw()` in `arch/loongarch/include/asm/io.h` is `mmiowb()`,
  so the barrier follows every non-relaxed write, not the unlock.
- ia64: there is no such directory under `arch/` in this tree.
- `mmiowb()`: has no generic definition; only some arch headers define it, so
  code that builds on every architecture cannot call it.
- `Documentation/driver-api/io_ordering.rst`: contains no `mmiowb()`; its fix
  is `(void)readl(safe_register)` before the unlock, and it calls that the
  driver's responsibility.
- `Documentation/driver-api/device-io.rst`: says posted writes are not
  strictly ordered against a spinlock; this and `io_ordering.rst` contradict
  guarantee 2 in `Documentation/memory-barriers.txt`.
- The code implements guarantee 2 with a barrier, not a read: the accessors
  and unlock paths above issue it where `spin_lock()` reaches
  `do_raw_spin_lock()` (not `CONFIG_PREEMPT_RT`, where `spin_lock()` is
  `rt_spin_lock()`), so `writel()` under `spin_lock()` without a read-back
  is not a missing barrier.
- `rwlock_t`: not covered; the hooks are only in `do_raw_spin_lock()`,
  `do_raw_spin_trylock()` and `do_raw_spin_unlock()`; `do_raw_write_lock()`
  and `do_raw_write_unlock()` in `include/linux/rwlock.h` have none.

**Posted writes**

- Read while the device may be resetting:
  `Documentation/driver-api/device-io.rst` says the flushing read may then be
  expected to fail and should be done from config space, which it calls
  guaranteed to soft-fail if the card does not respond.
- The document does not recommend choosing an MMIO register that is safe to
  read during reset.
- `ioremap_np()`: the generic version in `include/asm-generic/io.h` returns
  `NULL`; only `arch/arm64/include/asm/io.h` provides a real non-posted
  mapping.
- `ioremap_np()` on PCI BARs: `device-io.rst` forbids it, since PCI memory
  writes are always posted; the read-back is the method there.

**Ordering against DMA memory**

- **Potentially unsafe usage**: `dma_wmb()` as the only barrier between a
  store to coherent DMA memory and `writel_relaxed()`.
  - Unsafe: in a driver that can be built for an architecture whose `writel()`
    uses a stronger barrier than `dma_wmb()`. For example, on arm with
    `CONFIG_ARM_DMA_MEM_BUFFERABLE`, `__iowmb()` is `wmb()`, which is
    `__arm_heavy_mb(st)`, while `dma_wmb()` is `dmb(oshst)`.
  - Safe: in code built only for arm64, where `__io_bw()` in
    `arch/arm64/include/asm/io.h` is `dma_wmb()`, so `writel()` is that
    barrier and then the raw store; `__arm_smmu_cmdq_issue_cmdlist()` does
    this, and `ARM_SMMU_V3` depends on `ARM64`.
  - Safe: `wmb()` and then `writel_relaxed()`, as
    `ice_xdp_ring_update_tail()` does; `__io_bw()` in
    `include/asm-generic/io.h` defaults to `wmb()`, so this is what the
    generic `writel()` does.
  - Safe: plain `writel()` after the last store, as in the `dma_wmb()` example
    in `Documentation/memory-barriers.txt`; the generic `writel()` runs
    `__io_bw()` before the store.
- `rmb()` after `readl_relaxed()`: matches the generic `readl()`, whose
  `__io_ar()` defaults to `rmb()`; `hns_nic_rx_poll_one()` does this.
- `Documentation/memory-barriers.txt` descriptor example: does not mention
  `writel_relaxed()`; its note says only that the `dma_wmb()`, `dma_rmb()`
  and `dma_mb()` barriers give no ordering for MMIO.
- `__iowmb()`, `__iormb()`: defined only by some architectures, for example
  `arch/arm64/include/asm/io.h`, which marks them as not for portable
  drivers; there they are the barriers `writel()` and `readl()` use, so they
  do order MMIO against memory.
- A missing barrier does not show on every architecture: powerpc defines
  `writel_relaxed()` as `writel()` and `readl_relaxed()` as `readl()`, so a
  test there proves nothing about the relaxed forms.

## Pointers and mappings

**ioremap variants**

| Call | What `include/asm-generic/io.h` supplies when the arch has none |
|---|---|
| `ioremap()` | without `CONFIG_MMU`: a cast of the physical address, with an empty `iounmap()`; with `CONFIG_MMU` and `CONFIG_GENERIC_IOREMAP`: `ioremap_prot()` with `__pgprot(_PAGE_IOREMAP)`; otherwise nothing |
| `ioremap_wc()` | a macro for `ioremap` |
| `ioremap_wt()` | a macro for `ioremap` |
| `ioremap_uc()` | an inline that returns `NULL` |
| `ioremap_np()` | an inline that returns `NULL` |
| `ioremap_cache()` | nothing; the generic header does not define it |

- `_PAGE_IOREMAP`: an architecture that uses the `CONFIG_GENERIC_IOREMAP`
  inline `ioremap()` must define it; that `ioremap()` does not use
  `pgprot_noncached()`.
- `ioremap_cache()` caller: builds only on an architecture that defines
  `ioremap_cache()` itself.
- `memremap()` with `MEMREMAP_WB`: the place where a missing `ioremap_cache()`
  becomes `ioremap()`; see `arch_memremap_wb()` in `kernel/iomem.c`, which tests
  `#ifdef ioremap_cache`. That body is under `#ifndef arch_memremap_wb`; an
  architecture that defines its own (for example riscv) does not run it.

**Managed mapping helpers**

- There is no devm_ioremap_np() here; the offset/size siblings of
  `devm_ioremap()` are `devm_ioremap_uc()` and `devm_ioremap_wc()`.
- `DEVM_IOREMAP_NP`: chosen only inside `__devm_ioremap_resource()` in
  `lib/devres.c`, when the type passed in is `DEVM_IOREMAP` and `res->flags`
  has `IORESOURCE_MEM_NONPOSTED`.
- `devm_ioremap_resource_wc()` on a resource with `IORESOURCE_MEM_NONPOSTED`:
  ignores the flag and maps with `ioremap_wc()`.
- `IORESOURCE_MEM_NONPOSTED` set, `ioremap_np()` returns `NULL` (the generic
  stub): `devm_ioremap_resource()` releases the region and returns `-ENOMEM`;
  it does not retry with `ioremap()`.
- `pci_remap_cfgspace()` in `include/linux/io.h`: the form that does fall back,
  `ioremap_np() ?: ioremap()`.
- `of_mmio_is_nonposted()` in `drivers/of/address.c`: has no configuration
  test; true when `nonposted-mmio` is on the node or on its direct parent
  only, and `__of_address_to_resource()` then sets the flag.
- `devm_ioremap_resource()` errors: `-EINVAL` for a `NULL` or non-
  `IORESOURCE_MEM` resource, `-ENOMEM` when the region name cannot be
  allocated, `-EBUSY` when the region request fails, `-ENOMEM` when the mapping
  fails.
- `devm_ioremap_resource()` logging: goes through `dev_err_probe()`; the
  `-ENOMEM` cases print nothing, see `__dev_probe_failed()` in
  `drivers/base/core.c`.
- Without `CONFIG_HAS_IOMEM`: `devm_ioremap_resource()` is an inline stub in
  `include/linux/device/devres.h` that returns `IOMEM_ERR_PTR(-EINVAL)`.
- Without `CONFIG_HAS_IOMEM`: `devm_ioremap()` has no stub; `lib/devres.c` is
  not built, and the declaration in `include/linux/io.h` stays.

**The iomem annotation**

- `IOMEM_ERR_PTR()`: defined in `include/linux/err.h`, not in
  `include/linux/io.h`.
- `IS_ERR()`, `PTR_ERR()`, `IS_ERR_OR_NULL()`, `PTR_ERR_OR_ZERO()` and
  `ERR_CAST()`: the parameter is `__force const void *`, so in-tree code
  passes an `__iomem` pointer with no cast, for example
  `pcim_iomap_regions()` in `drivers/pci/devres.c`.
- Removing `__iomem`: in-tree code uses a `__force` cast, for example
  `arch_memremap_wb()` in `kernel/iomem.c` and `devm_iounmap()` in
  `lib/devres.c`.
- Adding `__iomem` to a plain pointer: in-tree code also does it with a plain
  cast and no `__force`, for example `memunmap()` in `kernel/iomem.c`; a missing
  `__force` on such a cast is not by itself a defect.
- `CHECKFLAGS` in the top-level `Makefile`: its only `-W` options are
  `-Wbitwise`, `-Wno-return-void` and `-Wno-unknown-attribute`, so no
  address-space warning beyond sparse's defaults is enabled.

## Model gaps

### Other mistakes models make

- Models take `pcim_iomap_regions()` and `pcim_iomap_table()` to be the
  current managed PCI mapping calls, and every `pcim_` mapping call to return
  `NULL` on failure. In `drivers/pci/devres.c` the kerneldoc marks both
  DEPRECATED. `pcim_iomap_region()` and `pcim_iomap_range()` return
  `IOMEM_ERR_PTR()`; `pcim_iomap()` returns `NULL`.
- Models take `inl()` and the other port accessors to be undefined without
  `CONFIG_HAS_IOPORT`. In `include/asm-generic/io.h` `inl` is still defined.
  `#ifdef inl` after that header is therefore always true.
- Models take `ioport_map()` without `CONFIG_GENERIC_IOMAP` to return
  `PCI_IOBASE + port` always. The inline in `include/asm-generic/io.h` first
  masks the port with `IO_SPACE_LIMIT`, and returns `NULL` above
  `MMIO_UPPER_LIMIT`. It exists only under `CONFIG_HAS_IOPORT_MAP`.
- Models take `ioread32()` to have one prototype. The `lib/iomap.c` version
  takes `const void __iomem *` and returns `unsigned int`. The inline version
  takes `const volatile void __iomem *` and returns `u32`. A `volatile` cookie
  therefore builds cleanly on one configuration and not on the other.
- Models take `ioread32_rep()` to have one count type. The count is
  `unsigned long` in `include/asm-generic/iomap.h` and `unsigned int` in
  `include/asm-generic/io.h`.
- Models take the MMIO trace hooks to depend on `CONFIG_TRACE_MMIO_ACCESS`
  alone and to be in every `readl()`. The option depends on
  `ARCH_HAVE_TRACE_MMIO_ACCESS`, which only arm64 and s390 select. Each call is
  also behind `rwmmio_tracepoint_enabled()`.
- Models take an architecture's own `readl()` to keep the trace hooks. Only the
  generic bodies call `log_read_mmio()`; the `readl()` in
  `arch/x86/include/asm/io.h`, for example, has no such call.
- Models know `CONFIG_INDIRECT_PIO` but not `CONFIG_INDIRECT_IOMEM`.
  `include/asm-generic/logic_io.h` tests it, and `arch/um/include/asm/io.h`
  includes that header.
- Models take the C headers to be the only code tied to the accessor names.
  `rust/helpers/io.c` wraps `readl()`, `writel()`, the relaxed forms,
  `memcpy_toio()` and `ioremap_np()` by name.
