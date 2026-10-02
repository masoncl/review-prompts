- Entries rewritten: every index from `num_wired_entries()` up, duplicated
  or not; `r4k_tlb_configure()`, the only caller, writes Wired to 0 first,
  so that is the whole TLB.
- Helpers: `r4k_tlb_uniquify_read()` only reads; `r4k_tlb_uniquify_write()`
  does every write.
- Values written: `(vpn << VPN2_SHIFT) | asid`, counted up from VPN 0,
  ASID 0; the ASID is incremented first, the VPN when `cpu_asid_mask()` is
  used up.
- Against `UNIQUE_ENTRYHI()`: the VPN is kept below
  `1 << (vmbits - VPN2_SHIFT)`, a user-segment address, while
  `UNIQUE_ENTRYHI()` is `CKSEG0`-based, so no index gives the same value.
- Against entries in the TLB: candidates are compared with the copy made by
  `r4k_tlb_uniquify_read()`, not with `tlb_probe()`.
- Recorded per entry in `struct tlbent`: VPN masked by that entry's own
  PageMask, page size, global bit, ASID (0 when global), wired, index.
- Wired or global entry reached by the candidate: the VPN is moved past the
  entry's whole span, whatever the ASID.
- Non-global entry with the same VPN and ASID: the ASID is incremented.
- User VPN space used up: `WARN_ON()`, `dump_tlb_all()`, and the write pass
  returns with the remaining entries not rewritten.
- EntryHi width: `read_c0_entryhi_native()` and `write_c0_entryhi_native()`
  use the 64-bit register when `cpu_has_64bits`, also with `CONFIG_32BIT`.
- Memory: an array of `tlbsize` `struct tlbent`, allocated and freed on
  each run.
  - `slab_is_available()` true: `kmalloc()` with `GFP_ATOMIC`, `kfree()`.
  - Otherwise: `memblock_alloc_raw()`, `memblock_free()`.
  - It uses neither `kmalloc_array()` nor `memblock_alloc()`.
