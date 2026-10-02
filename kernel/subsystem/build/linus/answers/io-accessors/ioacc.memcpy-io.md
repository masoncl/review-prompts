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
