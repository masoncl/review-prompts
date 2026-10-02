- There is no gicv5_its_write_dte() or gicv5_its_write_itte() here.

| Entry | Bit | Set in | Cleared in |
|---|---|---|---|
| L1 DTE | `GICV5_DTL1E_VALID` | `gicv5_its_alloc_l2_devtab()` | nowhere |
| L2 or linear DTE | `GICV5_DTL2E_VALID` | `gicv5_its_device_register()` | `gicv5_its_device_unregister()`; failed-invalidate path of `gicv5_its_device_register()` |
| L1 ITTE | `GICV5_ITTL1E_VALID` | `gicv5_its_create_itt_two_level()` | nowhere |
| L2 or linear ITTE | `GICV5_ITTL2E_VALID` | `gicv5_its_map_event()` | `gicv5_its_unmap_event()` |

- `gicv5_its_unmap_event()`: clears only `GICV5_ITTL2E_VALID` by
  read-modify-write; the LPI ID stays in the entry.
- DTE clears: both write the whole entry to 0.
- L1 ITTEs: stored with `WRITE_ONCE()` directly, all at ITT creation, then
  one `gicv5_its_dcache_clean()` over the L1 table.
- L1 ITT: never invalidated entry by entry; `gicv5_its_free_itt()` frees it.
- L2 device tables: never freed; for a two-level table
  `gicv5_its_deinit_devtab()` frees only the L1 table and the `l2ptrs`
  array.
- L1 IST entry, in `drivers/irqchip/irq-gic-v5-irs.c`: the IRS sets
  `GICV5_ISTL1E_VALID`, not software; `gicv5_irs_iste_alloc()` asks for it by
  writing the LPI ID, in `GICV5_IRS_MAP_L2_ISTR_ID`, to
  `GICV5_IRS_MAP_L2_ISTR`; see "Level 1 entry valid bit".
- Non-coherent IRS: `gicv5_irs_iste_alloc()` runs `dcache_inval_poc()` on
  the L1 entry after the poll, so that a later read sees the bit the IRS
  wrote.
- No code clears a valid L1 IST entry or frees a mapped L2 IST.
- Linear IST: has no L1 entries; `gicv5_irs_iste_alloc()` returns 0 at once
  when `gicv5_global_data.ist.l2` is false.
- Table base: software sets `GICV5_IRS_IST_BASER_VALID` for the IST;
  `GICV5_ITS_DT_BASER` is written with the address only, and the ITS is
  turned on with `GICV5_ITS_CR0_ITSEN` in `gicv5_its_enable()`.
