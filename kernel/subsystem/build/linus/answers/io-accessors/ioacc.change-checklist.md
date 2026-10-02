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
