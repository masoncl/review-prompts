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
