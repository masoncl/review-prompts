- `GICV5_ISTL1E_VALID`: set by the IRS, as a result of the write to
  `GICV5_IRS_MAP_L2_ISTR`; the driver never stores it.
- Driver's store: the level 2 physical address masked with
  `GICV5_ISTL1E_L2_ADDR_MASK`, valid clear; 0 after a failed wait.
- `GICV5_ISTL1E_L2_ADDR_MASK`: keeps bits 55:12, so a level 2 address that
  is not 4K aligned is truncated without warning.
- Access style in `gicv5_irs_iste_alloc()`: a plain load with
  `le64_to_cpu()` and a plain store with `cpu_to_le64()`; it uses neither
  `READ_ONCE()` nor `WRITE_ONCE()`.
- A valid level 1 entry makes `gicv5_irs_iste_alloc()` return 0 without
  writing `GICV5_IRS_MAP_L2_ISTR`; that test is the driver's only record
  that a block is mapped.
