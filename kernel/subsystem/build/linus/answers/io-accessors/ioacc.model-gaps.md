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
