- `gicv5_ppi_irq_mask()` and `gicv5_ppi_irq_unmask()`: both end with
  `isb()`; neither uses `gsb_sys()`.
- PPI mask comment: the disable must take effect immediately for lazy
  disable to work, and a context synchronization event guarantees it.
- PPI unmask comment: the enable must take effect in finite time, and a
  context synchronization event cannot be taken for granted, for example a
  core going straight into idle.
- Both PPI comments cite `I_ZLTKB/R_YRGMH`; the SPI/LPI comments cite
  `R_XCLJC`.
