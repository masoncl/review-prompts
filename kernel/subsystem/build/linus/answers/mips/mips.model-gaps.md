- Models take other CPUs' contexts to be zeroed by every SMP flush. Without
  MMID, in the branch that sends no IPI, `flush_tlb_mm()` in
  `arch/mips/kernel/smp.c` writes 0, but `flush_tlb_page()` writes 1 and
  `flush_tlb_range()` writes 0 only for a `VM_EXEC` VMA.
- Models take every routine that loads EntryHi for a probe to save the
  register and write it back. `__update_tlb()` in `arch/mips/mm/tlb-r4k.c`
  saves nothing: without MMID it leaves the address in EntryHi with the ASID
  field it read there; with `cpu_has_mmid` it leaves the bare address and
  does not touch MemoryMapID.
- Models take `arch/mips/mm/tlbex.c` to share `UNIQUE_ENTRYHI()` with the
  flush code. It never uses the macro.
- Models take `cpu_has_mmid` to be fixed once the boot CPU is probed.
  `cpu_disable_mmid()` in `arch/mips/kernel/cpu-probe.c` clears
  `MIPS_CPU_MMID` later, reached from `cps_prepare_cpus()` through
  `mips_cm_update_property()`; under `CONFIG_GENERIC_ATOMIC64` the macro is
  the constant 0.
- Models take wired-count setup to be permanent. `r4k_tlb_pm_notifier()`
  calls only `r4k_tlb_configure()`, which writes Wired 0, so the `ntlb=`
  limit set in `tlb_init()` is dropped.
- Models list CONFIG_CPU_XLR among the configurations with empty barriers.
  No such symbol exists here.
- Models know `kmap_coherent()` as the only open-coded wired entry.
  `kmap_noncoherent()` is a second one, called from
  `arch/mips/kernel/pm-cps.c`.
- Models take `dump_tlb_all()` to print every entry. `dump_tlb()` in
  `arch/mips/lib/dump_tlb.c` skips, among others, non-global entries whose
  ASID or MMID is not the current one.
