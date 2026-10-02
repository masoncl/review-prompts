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
