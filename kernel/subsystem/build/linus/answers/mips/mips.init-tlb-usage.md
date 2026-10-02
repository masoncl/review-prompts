- **Potentially unsafe usage**: `tlb_write_indexed()` of
  `UNIQUE_ENTRYHI(idx)` into a TLB that holds entries the kernel did not
  write.
  - Unsafe: when `cpu_has_tlbinv` is false and the inherited entries have
    not been rewritten first; an entry at another index can already hold
    the same `CKSEG0`-based value, and the duplicate raises a machine check.
  - Safe: after `r4k_tlb_uniquify()` has moved every entry to a user-segment
    value; `r4k_tlb_configure()` calls it before `local_flush_tlb_all()`.
    It rewrites nothing if its allocation fails, and stops early if the
    user VPNs run out.
  - Safe: when `cpu_has_tlbinv` is true; `UNIQUE_ENTRYHI()` then sets
    `MIPS_ENTRYHI_EHINV`, or `local_flush_tlb_all()` uses `tlbinvf()`, and
    `r4k_tlb_configure()` relies on that when it skips
    `r4k_tlb_uniquify()`.
- Writing back an inherited value: not done; `r4k_tlb_uniquify_read()`
  writes nothing, and `r4k_tlb_uniquify_write()` writes only an EntryHi it
  computed, with EntryLo0/1 of 0.
- Other callers of `tlb_read()` under `arch/mips`: none writes back the
  EntryHi it read; `dump_tlb()` only reads, and
  `kvm_vz_local_flush_roottlb_all_guests()` writes `UNIQUE_ENTRYHI(entry)`.
- `tlb_probe()`: `r4k_tlb_uniquify()` and `local_flush_tlb_all()` never
  call it; `r4k_tlb_uniquify_read()` learns the contents by index with
  `tlb_read()`, between `mtc0_tlbr_hazard()` and `tlb_read_hazard()`.
- `tlb_write_random()`: its only callers under `arch/mips` are the two
  `__update_tlb()` functions, in `arch/mips/mm/tlb-r4k.c` and
  `arch/mips/mm/tlb-r3k.c`; no initialisation code uses it.
- Interrupts: `r4k_tlb_uniquify()` and `r4k_tlb_configure()` do not disable
  them around their TLB accesses; `local_flush_tlb_all()` does, with
  `local_irq_save()`.
