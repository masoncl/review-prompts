- `UNIQUE_GUEST_ENTRYHI()`: base is `CKSEG1`; `UNIQUE_ENTRYHI()` uses `CKSEG0`.
  Both come from `_UNIQUE_ENTRYHI()` in `arch/mips/include/asm/tlb.h`.
- `MIPS_ENTRYHI_EHINV`: ORed in by `_UNIQUE_ENTRYHI()` itself when
  `cpu_has_tlbinv`; callers add nothing. `cpu_has_xpa` plays no part.
- Distinctness: holds only among entries written through the macro with
  different indexes; it says nothing about values firmware left in the TLB.
- `local_flush_tlb_all()` with `cpu_has_tlbinv` and a wired count of 0: writes
  no `UNIQUE_ENTRYHI()` value; it uses `tlbinvf()` instead.
- `build_huge_handler_tail()` in `arch/mips/mm/tlbex.c`, when `cpu_has_ftlb`
  and its `flush` argument is non-zero: ORs `MIPS_ENTRYHI_EHINV` into the live
  EntryHi, writes the entry, then clears the bit. The VPN2 is not made unique
  there.
- `arch/mips/mm/tlb-r3k.c`: uses neither macro. Only `local_flush_tlb_from()`
  writes a per-index value; the probe-based flushes write plain `KSEG0` for
  every entry.
