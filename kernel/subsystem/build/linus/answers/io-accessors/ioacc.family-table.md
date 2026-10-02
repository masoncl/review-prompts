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
