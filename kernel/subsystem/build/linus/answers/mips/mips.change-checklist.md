- Selection: at build time only, in `arch/mips/mm/Makefile`. `tlb-r4k.o` is
  built for `CONFIG_CPU_R4K_CACHE_TLB`, `CONFIG_CPU_SB1` and
  `CONFIG_CPU_CAVIUM_OCTEON`; `tlb-r3k.o` for `CONFIG_CPU_R3K_TLB`, which
  `CPU_R3000` selects. There is no CPU_TX39XX in this tree.
- `arch/mips/mm/tlb-r3k.c`: not a routine-for-routine twin. It defines no
  `local_flush_tlb_one()`, flushes single pages with one EntryLo, and uses
  neither `htw_stop()` nor `UNIQUE_ENTRYHI()`.
- Copies of the TLB write sequence outside `tlb-r4k.c`: search `arch/mips`
  for `tlb_write_indexed()`. For example `_kvm_mips_host_tlb_inv()` in
  `arch/mips/kvm/tlb.c` and `kunmap_coherent()` in `arch/mips/mm/init.c`.
- `arch/mips/kernel/smp.c` with `cpu_has_mmid`: `flush_tlb_all()`,
  `flush_tlb_range()` and `flush_tlb_page()` use ginvt and never reach
  `tlb-r4k.c`, so a fix to a local routine does not cover them.
- `dump_tlb()` in `arch/mips/lib/dump_tlb.c`: depends on what a flushed
  entry looks like; it skips entries with `MIPS_ENTRYHI_EHINV` (when
  `cpu_has_tlbinv`) and entries whose EntryHi equals `CKSEG0` once the low
  17 bits are masked.
- Dump code, which file: `dump_tlb.o` is built for
  `CONFIG_CPU_GENERIC_DUMP_TLB` (default y unless `CPU_R3000`),
  `r3k_dump_tlb.o` for `CONFIG_CPU_R3000`.
- Dump callers: search for `dump_tlb_all()`. No debugfs, procfs or sysfs
  file in `arch/mips` calls it.
- SysRq `x`: registered in `arch/mips/kernel/sysrq.c`, with enable mask
  `SYSRQ_ENABLE_DUMP`; dumps on every CPU.
- `DEBUG_TLB` in `arch/mips/mm/tlb-r3k.c`: compile-time `printk()` tracing,
  `#undef` by default; `tlb-r4k.c` has no equivalent.
