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
