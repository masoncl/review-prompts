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
