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
