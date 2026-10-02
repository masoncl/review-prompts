- `gicv5_global_data.ist`: written after the `GICV5_IRS_IST_CFGR` write and
  before the `GICV5_IRS_IST_BASER` write; the linear path sets only `l2`.
- Coherent IRS: `dsb(ishst)` takes the place of the cache clean, before
  either register write; both register writes are relaxed.
- IST already valid: `gicv5_irs_init_ist()` tests
  `GICV5_IRS_IST_BASER_VALID` before anything else, prints an error and
  returns `-EPERM`; it neither adopts nor tears down the table.
- That `-EPERM` fails `gicv5_irs_enable()` and so `gicv5_init_common()`.
- `GICV5_IRS_IST_BASER`: written only by the two table init functions, with
  valid set; no code in this tree writes it with valid clear, including
  `gicv5_irs_remove()` and the failed-wait path.
- `kmemleak_ignore()` on success: called for the linear table; not called
  for the level 1 table, which stays reachable through
  `gicv5_global_data.ist.l1ist_addr`.
