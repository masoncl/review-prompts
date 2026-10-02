- EPPI: `convert_offset_index()` leaves the offset unchanged and returns
  index = hwirq - `EPPI_BASE_INTID` + 32; only ESPI gets a remapped offset.
- Callers pass the `GICD_` offset names for redistributor interrupts too;
  there is no GICR_ISENABLERnE in this tree.
- ESPI offsets that `convert_offset_index()` remaps: `GICD_ISENABLER`,
  `GICD_ICENABLER`, `GICD_ISPENDR`, `GICD_ICPENDR`, `GICD_ISACTIVER`,
  `GICD_ICACTIVER`, `GICD_IPRIORITYR`, `GICD_ICFGR`, `GICD_IROUTER`.
- `GICD_IGROUPR` and `GICD_IGRPMODR` are not remapped.
- `convert_offset_index()` does no scaling: it returns the bank offset and an
  index relative to the bank; each caller turns the index into a register
  and bit (`gic_configure_irq()` does it for `GICD_ICFGR`).
- `convert_offset_index()` cannot fail: on an unknown ESPI offset, an LPI or
  an invalid range it does `WARN_ON(1)` and returns the unchanged offset with
  the raw hwirq as index, and the caller performs the access.
- `gic_dist_base()`: called only by `gic_irq_set_prio()` and
  `gic_set_affinity()`; neither tests the `NULL` it returns for an LPI.
- `gic_peek_irq()`, `gic_poke_irq()`, `gic_set_type()`: pick the frame with
  `gic_irq_in_rdist()`, which sends every other range to the distributor.
- Distributor accesses in `gic_peek_irq()` and `gic_set_type()` (the read
  and the write of `GICD_ICFGR`) go through `gic_dist_base_alias()`; writes
  in `gic_poke_irq()` use `gic_data.dist_base`.
- `gic_dist_base_alias()` with `gic_nvidia_t241_erratum` enabled: handles
  SPI and ESPI only, `unreachable()` for any other range.
- SGI, PPI and EPPI frame: `gic_data_rdist()` is `this_cpu_ptr()`, so the
  access reaches the copy of the interrupt owned by the executing CPU.
- `__get_intid_range()`: `LPI_RANGE` ends at `GENMASK(23, 0)`; above that is
  `__INVALID_RANGE__`, while the callbacks test `hwirq >= 8192`.
- No check against implemented counts: neither `gic_irq_domain_translate()`
  nor `gic_irq_domain_map()` compares hwirq with `GIC_LINE_NR`,
  `GIC_ESPI_NR` or `gic_data.ppi_nr`; those bound only the init loops in
  `gic_dist_init()` and `gic_cpu_init()`.
- `gic_irq_domain_map()`: maps an LPI when `gic_dist_supports_lpis()`;
  -EPERM only otherwise and for `__INVALID_RANGE__`.
- There is no gic_get_ppi_index() or __gic_get_ppi_index() here, and
  `gic_irq_nmi_setup()` keeps no per-PPI refcount.
- **Unsafe usage**: passing `convert_offset_index()` an offset outside its
  ESPI switch for an interrupt that can be an ESPI.
  - Safe: write the `nE` bank directly with an index from 0, as
    `gic_dist_init()` does for `GICD_IGROUPRnE`.
- **Potentially unsafe usage**: a chip callback that calls `gic_peek_irq()`,
  `gic_poke_irq()` or `gic_dist_base()` without testing the range.
  - Unsafe: in a callback that a child domain forwards for an LPI;
    `its_irq_chip` forwards `irq_eoi` with `irq_chip_eoi_parent()`. The
    access then uses the raw hwirq as index.
  - Safe: test first, as `gic_eoimode1_eoi_irq()` (`hwirq >= 8192`) and
    `gic_arm64_erratum_2941627_needed()` (range is SPI or ESPI) do.
  - Safe: a callback that every chip above an LPI implements itself, for
    example `gic_mask_irq()`; `its_irq_chip`, `its_vpe_irq_chip` and
    `its_vpe_4_1_irq_chip` each have their own `irq_mask`.
