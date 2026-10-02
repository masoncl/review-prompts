- `gicv5_irs_ist_synchronise()`: only polls `GICV5_IRS_IST_STATUSR` for
  `GICV5_IRS_IST_STATUSR_IDLE`; it writes no register and does no cache
  maintenance.
- Poll timing: `gicv5_wait_for_op_s_atomic()` in
  `include/linux/irqchip/arm-gic-v5.h` polls every 1 µs for
  `10 * USEC_PER_MSEC` µs (10 ms), then returns `-ETIMEDOUT`.
- Ordering of poll and `dcache_inval_poc()`: the driver adds no explicit
  barrier; it relies on the non-relaxed `readl()` inside
  `readl_poll_timeout_atomic()`, whose `__io_ar()` in
  `arch/arm64/include/asm/io.h` is `dma_rmb()` plus a control dependency.
- **Unsafe usage**: polling for completion with `readl_relaxed()` before
  invalidating or reading memory the IRS wrote.
  - Safe: poll with `gicv5_wait_for_op_atomic()`, as
    `gicv5_irs_ist_synchronise()` does.
- Only readback site: the level 1 entry tested in `gicv5_irs_iste_alloc()`;
  the driver keeps no pointer to the linear table or to any level 2 table.
- Invalidated range: one 8-byte entry, less than a cache line, so
  `dcache_inval_poc()` cleans as well as invalidates the line; see
  `__dcache_inval_poc_nosync` in `arch/arm64/mm/cache.S`.
- **Potentially unsafe usage**: `dcache_inval_poc()` over a single level 1
  entry.
  - Unsafe: when the CPU has stored to that cache line since it was last
    cleaned; the clean writes the CPU's copy back over what the IRS wrote.
  - Safe: after `dcache_clean_poc()` of the entry with no store in between,
    as on the success path of `gicv5_irs_iste_alloc()`.
