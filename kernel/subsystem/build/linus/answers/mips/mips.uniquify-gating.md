- `r4k_tlb_configure()`: the only test on the call is `!cpu_has_tlbinv`;
  there is no second condition for a TLB that reset leaves clean.
- `r4k_tlb_configure()` tests none of `cpu_has_ftlb`, `cpu_has_mmid` or
  `cpu_has_mips_r6` before the call; the `MIPS_CPU_TLBINV` bit or a platform
  override alone decides.
- Not handled by `r4k_tlb_uniquify()`:
  - FTLB: it writes any VPN to any index and never reads `tlbsizevtlb`.
  - MMID: it takes the ASID from EntryHi with `cpu_asid_mask()` and never
    touches `read_c0_memorymapid()`.
  - R6 without a 4KiB page size: it writes `PM_4K` entries.
- Inherited large pages: handled; the read pass records each entry's
  PageMask and the write pass moves the VPN past the span of an entry it
  steps over.
- Hardware page-table walker: handled; `r4k_tlb_uniquify()` calls
  `htw_stop()` before its read pass and `htw_start()` after its write pass.
