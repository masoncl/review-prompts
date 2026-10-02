- EntryLo0 and EntryLo1: zeroed before the `idx < 0` test, so the registers
  are clobbered on a probe miss too; a miss skips only the
  `UNIQUE_ENTRYHI()` write, `tlb_write_indexed()` and their barriers.
- `cpu_has_tlbinv`: the single-entry routines never execute `tlbinvf()`;
  only `local_flush_tlb_all()` does, and only with no wired entries. Here
  the invalid mark comes from `MIPS_ENTRYHI_EHINV`, which `UNIQUE_ENTRYHI()`
  in `arch/mips/include/asm/tlb.h` ORs in.
- PageMask of the overwritten entry: whatever the register holds, since the
  routines do not set it. `r4k_tlb_configure()` sets `PM_DEFAULT_MASK`, and
  code that changes the register puts it back, for example the huge-page
  branch of `__update_tlb()` and `add_wired_entry()`.
